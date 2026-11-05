$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$docx=Join-Path $projectRoot 'docs/ai-update/final-report/ShieldVI_Tom_tat_de_tai_2_trang.docx'
$pdf=Join-Path $projectRoot 'docs/ai-update/final-report/ShieldVI_Tom_tat_de_tai_2_trang.pdf'
$word=$null
$document=$null
function Stage($message){Add-Content -LiteralPath (Join-Path $PSScriptRoot 'project_brief_20261105_render_stages.log') -Value ((Get-Date -Format o)+' '+$message) -Encoding UTF8}
try {
  Stage 'Create isolated Word automation'
  $word=New-Object -ComObject Word.Application
  $word.Visible=$false
  $word.DisplayAlerts=0
  $word.AutomationSecurity=3
  Stage 'Open generated DOCX'
  $document=$word.Documents.Open($docx,$false,$false,$false)
  Stage 'Update fields'
  $document.Fields.Update() | Out-Null
  Stage 'Repaginate'
  $document.Repaginate()
  Stage 'Count pages'
  $pageCount=$document.ComputeStatistics(2)
  $pageSummaries=@()
  for($pageIndex=1;$pageIndex -le $pageCount;$pageIndex++) {
    $pageStart=$document.GoTo(1,1,$pageIndex).Start
    $pageEnd=if($pageIndex -lt $pageCount){$document.GoTo(1,1,($pageIndex+1)).Start}else{$document.Content.End}
    $pageText=$document.Range($pageStart,$pageEnd).Text
    $pageSummaries+=@{page=$pageIndex;characters=$pageText.Length;ending=$pageText.Substring([Math]::Max(0,$pageText.Length-115))}
  }
  Stage 'Save DOCX'
  $document.Save()
  $receipt=@{status=if($pageCount -eq 2){'PASS'}else{'NEEDS_LAYOUT_ADJUSTMENT'};renderer='Microsoft Word';pages=$pageCount;page_summaries=$pageSummaries;docx=$docx;pdf_exported=$false}
  $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'project_brief_20261105_word_render.json') -Encoding UTF8
  $receipt | ConvertTo-Json -Depth 5
} finally {
  if($document){$document.Close(0);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($document)}
  if($word){$word.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)}
}
