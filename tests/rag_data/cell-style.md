# Change Cell Styles

A tutorial showing how to change the style of cells in a SpreadJS ReportSheet, including background colors or borders with UI and code examples

## Content

When creating a report, it is important to set some background color or border for some cells to enhance the UI of the report. In the ReportSheet, the style of the cell matches the style of the corresponding template cell. You can set styles in the **TemplateSheet** for the content that needs to be highlighted, either as an expanded cell or as a non-expanded cell.

> **Notes**:
>
> * If you set the style on a non-extended cell in the TemplateSheet, the range affected by the style will not change on the DataEntryPreview render mode of the ReportSheet, but the position corresponding to the style's appearance will change offset.
> * If you set the style on an extended cell in the TemplateSheet, then on the DataEntryPreview render mode of the ReportSheet, the range affected by the style will change and the position corresponding to the appearance of the style will be offset.

The following code samples show how to set different cell styles.

```
// Header Style
const headerStyle = new GC.Spread.Sheets.Style();
headerStyle.backColor = '#bfdbd8';
headerStyle.foreColor = '#424242';
headerStyle.hAlign = GC.Spread.Sheets.HorizontalAlign.center;
headerStyle.vAlign = GC.Spread.Sheets.HorizontalAlign.center;
headerStyle.font = '12px Maine';

// Column 1 Style
const style1 = new GC.Spread.Sheets.Style();
style1.vAlign = GC.Spread.Sheets.VerticalAlign.center;
style1.hAlign = GC.Spread.Sheets.HorizontalAlign.center;
style1.backColor = "lightgrey";

// Column 2 Style
const style2 = new GC.Spread.Sheets.Style();
style2.vAlign = GC.Spread.Sheets.VerticalAlign.center;
style2.hAlign = GC.Spread.Sheets.HorizontalAlign.center;
style2.borderTop = new GC.Spread.Sheets.LineBorder("black", GC.Spread.Sheets.LineStyle.thin);
style2.borderBottom = new GC.Spread.Sheets.LineBorder("black", GC.Spread.Sheets.LineStyle.thin);
style2.font = '12px Maine';
style2.backColor = '#edebeb';

// Column 3 Style
const style3 = new GC.Spread.Sheets.Style();
style3.backColor = 'whitesmoke';
style3.borderLeft = new GC.Spread.Sheets.LineBorder("black", GC.Spread.Sheets.LineStyle.thin);
style3.borderTop = new GC.Spread.Sheets.LineBorder("black", GC.Spread.Sheets.LineStyle.thin);
style3.borderRight = new GC.Spread.Sheets.LineBorder("black", GC.Spread.Sheets.LineStyle.thin);
style3.borderBottom = new GC.Spread.Sheets.LineBorder("black", GC.Spread.Sheets.LineStyle.thin);

// Set the Styles
templateSheet.getRange('A1:C1').setStyle(headerStyle);

// The style set in the template sheet will be expanded with the current cell
templateSheet.getRange('A2').setStyle(style1);
templateSheet.getRange('B2').setStyle(style2);
templateSheet.getRange('C2').setStyle(style3);
```

The output of the above code will look like below.
![RS-cellStyles](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/ef9b66d1-0ae2-4e94-b8cb-f9f893aacc8d/RS-cellStyles.d9734f.png?width=668)