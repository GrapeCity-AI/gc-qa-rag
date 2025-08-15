# Check Box Cell

A tutorial showing how to work with Check Box cell types in SpreadJS, including the different options available, such as alignment and wordwrap

## Content

You can display a check box in a cell using the check box cell. A check box cell displays a small check box that can have one of three states, checked, unchecked, or indeterminate. You can customize the check box by setting the text.
Set the [isThreeState](gcdocsite__documentlink?toc-item-id=9c6c313f-1184-4a74-87b1-b51775c97386#isThreeState) method to true to display three states instead of two (checked or unchecked). You can also specify the alignment of the check box and the text with the [textAlign](gcdocsite__documentlink?toc-item-id=9c6c313f-1184-4a74-87b1-b51775c97386#textAlign) method.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/cellcheckbox.png)

You can set the state of the check box in code with the [value](gcdocsite__documentlink?toc-item-id=64f05fd4-fafa-47dc-9856-b74263f357ec#value) method as shown in the following table:

| **Value** | **State**     |
| --------- | ------------- |
| `null `   | Indeterminate |
| `0 `      | Unchecked     |
| `1 `      | Checked       |

You can change the size of a check box using the **boxSize()** method whose value can be set to any number or "auto". If the method is set to any invalid value, the check box size is not changed. The standard size of a check box in the check box cell type is 12\*12.

### Using Code

This example creates a check box cell with three states.

```javascript
// Get the activesheet
var activeSheet = spread.getSheet(0);
var cellType = new GC.Spread.Sheets.CellTypes.CheckBox();
cellType.caption("caption");
cellType.textTrue("True");
cellType.textFalse("False");
cellType.textIndeterminate("Indeterminate");
cellType.textAlign(GC.Spread.Sheets.CellTypes.CheckBoxTextAlign.bottom);
cellType.isThreeState(true);
cellType.boxSize(20);
activeSheet.getCell(1, 1).cellType(cellType);
//activeSheet.getCell(1, 1).value(1);
```

## Wrap Text in CheckBox Cell

In the scenarios where the check box captions are too long to fit in a cell then to wrap the displayed text, you need to set the cell style **wordWrap** property to true. The **wordWrap** property is set to false by default.

| **wordWrap property** | **Output**                                                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **wordWrap** = false  | ![wordWrap_false](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/wordWrap_false.a6ede2.PNG?width=200) |
| **wordWrap** = true   | ![wordWrap_true](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/wordWrap_true.1db0f2.PNG?width=200)   |

The line break rule followed in the check box cell is such that it initially breaks the content by words and, if necessary, further breaks the inner word to fit the available space.
![wordWrap_innerWordBreak](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/wordWrap_innerWordBreak.d51d01.PNG?width=200)
If **wordWrap** in check box cell is enabled and the vertical alignment of the cell is set, then the check box will be displayed as below:

| **Vertical alignment**                                                               | **Output**                                                                                                                                                         |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| If cell vAlign is top, then the check box will align at the top with the text.       | ![wordWrap_true](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/wordWrap_true.08d8f5.PNG?width=200)               |
| If cell vAlign is middle, then the check box will align in the middle with the text. | ![wordWrap_middleAlign](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/wordWrap_middleAlign.f596f7.PNG?width=200) |
| If cell vAlign is bottom, then the check box will align at the bottom with the text. | ![wordWrap_bottomAlign](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/wordWrap_bottomAlign.f325dc.PNG?width=200) |

However, you can change the horizontal alignment of the wrapped text based on the cell's hAlign value. For example, if the cell's hAlign is set to right, only the caption text will align to the right of the cell. Similarly, if cell's hAlign is set to left or center, only the caption text alignment is changed to left or center.

### Using Code

This example implements **wordWrap** in the check box cell.

```javascript
// set the long caption
cellType.caption("This is a very very long long text"); 
activeSheet.getCell(1, 1).cellType(cellType); 
activeSheet.setRowHeight(1, 120); 
activeSheet.setColumnWidth(1, 110); 
// set the wordwrap property to true
activeSheet.getCell(1, 1).wordWrap(true);
```