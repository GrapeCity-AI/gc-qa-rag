# Button Cell

A tutorial showing how to work with Button cell types in SpreadJS

## Content

You can display a button in a cell using the button cell. You can also set appearance properties such as color and text.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/cellbutton.png)

## Using Code

This example creates a button cell and sets the cell backcolor.

```javascript
var cellType = new GC.Spread.Sheets.CellTypes.Button();
cellType.buttonBackColor("#FFFF00");
cellType.text("this is a button");
activeSheet.getCell(0, 2).cellType(cellType);
```