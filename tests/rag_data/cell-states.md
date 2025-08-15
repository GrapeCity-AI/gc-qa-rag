# Cell States

A tutorial showing the different types of cell states available in SpreadJS, including the enumerations, priority ordering, and code examples

## Content

SpreadJS allows users to configure custom cell styles when the cell state is matched in a specific state like edit, hover, active, select, etc. This feature is helpful in creating input form controls, advanced structured forms, and other interactive forms within the spreadsheet where you want to specify cell styles according to the current state of the cell.

Cell States represent how a cell will respond to different actions from the user. Typically, cell state is a part of style and users can create custom-named styles to apply various cell features selectively and easily. By implementing cell states, users can create modern user interfaces for spreadsheet-based forms and interactive dashboards. Users can also highlight the active row and column for the selected/active cell and work with applications in real-time. Further, you can also mark the cells whose value is an [invalid formula string.](gcdocsite__documentlink?toc-item-id=53060fc8-0e90-484e-bd0a-6fe7b2f62bc6)

**Example** \- The following screenshot depicts different cell styles when a user hovers over a cell\, selects a cell\, or changes the state of a cell in a spreadsheet\. In this example\, the background color of the cell changes to pink\, and the foreground color of the cell changes to red when the cell is in a hover state\. The cell color changes to yellow when a cell is selected and the back color changes to blue and the fore color to red when the cell state is dirty\.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/cellstate.gif)

## Types of Cell States

The [CellStatesType](gcdocsite__documentlink?toc-item-id=2af91a4b-28af-4ef5-8ae4-9e34f4e2b414) enumeration can be used to work with different cell states in the spreadsheet, as described in the table shared below:

| **Enum Type and Value** | **Description** |
| ------------------- | ----------- |
| hover = 0x01 | Executes the specified action when the mouse hovers on a cell. |
| invalid = 0x02 | Sets the cell state to invalid if the conditional evaluation fails during data validation. |
| readonly = 0x04 | Locks the cell in a protected worksheet. |
| edit = 0x08 | Executes the specified action when the cell is being edited. |
| active = 0x10 | Executes the specified action when the cell is in focus. |
| selected = 0x20 | Executes the specified action when the cell is lying in the selected range of the worksheet. |
| dirty = 0x40 | Sets a cell state to dirty on changing the cell value or the reference cell value, to easily track any change in the sheet data. |
| invalidFormula = 0x80 | Mark the cell with an invalid formula string. |

## Priority Ordering

While configuring different cell styles for various cell states in the worksheet, the priority is followed in the below order:

edit > hover > active > selected > invalid formula > dirty > invalid > read-only

where the cell in the normal state will have the least priority and the cell in edit mode will have the highest priority.

If cell state styles for two different cell ranges intersect with each other, then the style which was last set by the user will possess more priority.

The following code sample shows how to apply different styles when users hover over a cell or select a cell in the spreadsheet.

```javascript
// initializing Spread
var spread = new GC.Spread.Sheets.Workbook(document.getElementById('ss'), { sheetCount: 1 });
// get the activesheet
var activeSheet = spread.getSheet(0);
// Adding Data to the spreadsheet
activeSheet.setValue(0, 1, "Y-2015");
activeSheet.setValue(0, 2, "Y-2016");
activeSheet.setValue(0, 3, "Y-2017");
activeSheet.setValue(0, 4, "Y-2018");
activeSheet.setValue(0, 5, "Y-2019");
activeSheet.setValue(1, 0, "Gradlco");
activeSheet.setValue(2, 0, "Saagiate");
activeSheet.setValue(3, 0, "Inferno");
activeSheet.setColumnWidth(0, 120);

// Creating a HoverStyle
var hoverStyle = new GC.Spread.Sheets.Style();
hoverStyle.backColor = "pink";
hoverStyle.foreColor = "red";

// Creating a SelectStyle
var selectStyle = new GC.Spread.Sheets.Style();
selectStyle.backColor = "yellow";
selectStyle.foreColor = "red";

// Creating a DirtyStyle
var dirtyStyle = new GC.Spread.Sheets.Style();
dirtyStyle.backColor = 'lightblue';
dirtyStyle.foreColor = 'red';

// Accessing cell range A1:J10
var range = new GC.Spread.Sheets.Range(0, 0, 10, 10);

// Applying styles on different CellStatesType
activeSheet.cellStates.add(range, GC.Spread.Sheets.CellStatesType.dirty, dirtyStyle);
activeSheet.cellStates.add(range, GC.Spread.Sheets.CellStatesType.selected, selectStyle);
activeSheet.cellStates.add(range, GC.Spread.Sheets.CellStatesType.hover, hoverStyle);
```