param(
  [Parameter(Mandatory=$true)][string]$Pptx,
  [Parameter(Mandatory=$true)][string]$Project,
  [Parameter(Mandatory=$true)][string]$Out,
  [ValidateSet('WPS','PowerPoint')][string]$Application = 'WPS',
  [string]$EditPlan
)
$ErrorActionPreference='Stop'
$projectPath=(Resolve-Path -LiteralPath $Project).Path
$pptxPath=(Resolve-Path -LiteralPath $Pptx).Path
$outPath=[IO.Path]::GetFullPath((Join-Path $projectPath $Out))
$insidePrefix=$projectPath.TrimEnd('\')+'\'
if(-not $outPath.StartsWith($insidePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output must remain inside project.' }
$rel=$outPath.Substring($insidePrefix.Length)
if($rel -notmatch '^(qa|tmp)[\\/]') { throw 'Render output must be under qa/ or tmp/.' }
if(Test-Path -LiteralPath $outPath) { throw 'Use a new render directory; do not overwrite evidence.' }
New-Item -ItemType Directory -Path $outPath | Out-Null
$spec=Get-Content -LiteralPath (Join-Path $projectPath 'spec\deck_spec.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$outputMode=$spec.output_mode
if(-not $outputMode -and $spec.schema_version -eq '2.1') { $outputMode='comparison' }
if($outputMode -notin @('editable_only','comparison')) { throw 'Invalid output_mode.' }
$expectedSlides=if($outputMode -eq 'editable_only') {1} else {2}
$editableSlide=$expectedSlides
if($spec.slides -ne $expectedSlides -or $spec.editable_slide -ne $editableSlide) { throw 'Slide mapping does not match output_mode.' }
$width=[int][Math]::Round($spec.design_px[0]); $height=[int][Math]::Round($spec.design_px[1])
$inputHash=(Get-FileHash -LiteralPath $pptxPath -Algorithm SHA256).Hash.ToLowerInvariant()
$receipt=[ordered]@{status='NOT_RUN';operation=$(if($EditPlan){'edit_test'}else{'render'});application=$Application;version=$null;pptx=$pptxPath;pptx_sha256=$inputHash;rendered_pptx_sha256=$null;slide_count=0;started_utc=[DateTime]::UtcNow.ToString('o');outputs=@();edits=@();limitations=@();error=$null}
$office=$null; $presentation=$null; $workingFile=$pptxPath
function Find-NamedShape($collection,[string]$target) {
  $hits=@()
  for($i=1;$i -le $collection.Count;$i++) {
    $candidate=$collection.Item($i)
    if($candidate.Name -eq $target) { $hits+=,$candidate }
    if($candidate.Type -eq 6) { $hits+=@(Find-NamedShape $candidate.GroupItems $target) }
  }
  return $hits
}
try {
  $edit=$null
  if($EditPlan) {
    $edit=Get-Content -LiteralPath (Resolve-Path -LiteralPath $EditPlan).Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if(-not $edit.test_only -or $edit.operations.Count -lt 1) { throw 'Edit tests require test_only=true and operations.' }
    $workingFile=Join-Path $outPath 'temporary-edit-test.pptx'
    Copy-Item -LiteralPath $pptxPath -Destination $workingFile
  }
  $progId=if($Application -eq 'WPS') {'KWPP.Application'} else {'PowerPoint.Application'}
  $office=New-Object -ComObject $progId
  $receipt.version=[string]$office.Version
  # Never Quit()/kill a shared Office process. Close only the presentation we open.
  # Open final files read-only, with no presentation window. Only a disposable test copy is writable.
  $readOnly=if($EditPlan) {0} else {-1}
  $presentation=$office.Presentations.Open($workingFile,$readOnly,0,0)
  $receipt.slide_count=$presentation.Slides.Count
  if($receipt.slide_count -ne $expectedSlides) { throw ('Expected '+$expectedSlides+' slides.') }
  if($edit) {
    foreach($operation in $edit.operations) {
      $found=@(Find-NamedShape $presentation.Slides.Item($editableSlide).Shapes $operation.shape_name)
      if($found.Count -ne 1) { throw ('Shape name is missing/ambiguous: '+$operation.shape_name) }
      $shape=$found[0]
      switch($operation.op) {
        'text' {
          if(-not $shape.HasTextFrame) { throw 'Not native text.' }
          $before=[string]$shape.TextFrame.TextRange.Text
          $shape.TextFrame.TextRange.Text=[string]$operation.value
          $after=[string]$shape.TextFrame.TextRange.Text
          if($after -ne [string]$operation.value) { throw 'Native text update failed.' }
          $receipt.edits+=@{op='text';shape_name=$shape.Name;before=$before;after=$after}
        }
        'move' {
          if($operation.require_group -and $shape.Type -ne 6) { throw 'Not a native group.' }
          $left=$shape.Left; $top=$shape.Top
          $shape.Left=$left+[double]$operation.dx_design_px*$presentation.PageSetup.SlideWidth/$spec.design_px[0]
          $shape.Top=$top+[double]$operation.dy_design_px*$presentation.PageSetup.SlideHeight/$spec.design_px[1]
          $receipt.edits+=@{op='move';shape_name=$shape.Name;before=@($left,$top);after=@($shape.Left,$shape.Top)}
        }
        'table_cell' {
          if(-not $shape.HasTable) { throw 'Not a native table.' }
          $cell=$shape.Table.Cell([int]$operation.row+1,[int]$operation.col+1).Shape.TextFrame.TextRange
          $before=[string]$cell.Text; $cell.Text=[string]$operation.value
          if($cell.Text -ne [string]$operation.value) { throw 'Native table edit failed.' }
          $receipt.edits+=@{op='table_cell';shape_name=$shape.Name;before=$before;after=[string]$cell.Text}
        }
        default { throw ('Unsupported edit test; requires a verified adapter: '+$operation.op) }
      }
    }
    $presentation.Save()
    $presentation.Close(); $presentation=$null
    $presentation=$office.Presentations.Open($workingFile,-1,0,0)
    $receipt.edited_pptx=$workingFile
    $receipt.edited_sha256=(Get-FileHash -LiteralPath $workingFile -Algorithm SHA256).Hash.ToLowerInvariant()
    $receipt.limitations+= 'Native operations executed and copy reopened; inspect rendered results for overflow, group/connector following and non-target preservation. Chart/math edit requires separate adapter.'
  }
  for($slideNo=1;$slideNo -le $expectedSlides;$slideNo++) {
    $png=Join-Path $outPath ('slide-'+$slideNo+'.png')
    $presentation.Slides.Item($slideNo).Export($png,'PNG',$width,$height)
    if(-not (Test-Path -LiteralPath $png) -or (Get-Item -LiteralPath $png).Length -eq 0) { throw 'Render file missing or empty.' }
    $receipt.outputs+=@{slide=$slideNo;path=$png;sha256=(Get-FileHash -LiteralPath $png -Algorithm SHA256).Hash.ToLowerInvariant()}
  }
  if((Get-FileHash -LiteralPath $pptxPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $inputHash) { throw 'Input hash unexpectedly changed.' }
  $receipt.rendered_pptx_sha256=(Get-FileHash -LiteralPath $workingFile -Algorithm SHA256).Hash.ToLowerInvariant()
  $receipt.status='PASS'
} catch {
  $receipt.status='FAIL'; $receipt.error=$_.Exception.Message
} finally {
  if($null -ne $presentation) { try {$presentation.Close()} catch {} }
  if($null -ne $presentation) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) }
  if($null -ne $office) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($office) }
  $receipt.completed_utc=[DateTime]::UtcNow.ToString('o')
  $receiptPath=Join-Path $outPath 'receipt.json'
  [IO.File]::WriteAllText($receiptPath,($receipt | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
}
$receipt | ConvertTo-Json -Depth 10
if($receipt.status -ne 'PASS') { exit 1 }
