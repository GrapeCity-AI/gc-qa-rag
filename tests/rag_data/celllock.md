# Protect Worksheet and Lock Cells

A tutorial showing how to protect worksheets and locks cells via properties, the Designer, and code in SpreadJS

## Content

SpreadJS allows you to protect a worksheet that locks all cells and prevents other users from changing, moving, or deleting the data. However, you can still copy the data from locked cells.
The **isProtected** option can be set to true to protect a worksheet and the [locked](gcdocsite__documentlink?toc-item-id=64f05fd4-fafa-47dc-9856-b74263f357ec#locked) method can be used to lock or unlock the cells.

## Unlock Cells in a Protected Worksheet

You can allow the user to edit specific cells in a protected worksheet by setting the **locked** method as False.

```js
sheet.getCell(1,1, GC.Spread.Sheets.SheetArea.viewport).locked(false);
sheet.setValue(1,1,"unLocked");
sheet.getRange(-1,3, -1, 1).locked(false);
sheet.getRange(5, -1, 1, -1).locked(false);
sheet.options.isProtected = true;
```

## Lock a Range of Cells in a Protected Worksheet

You can choose to lock a specific range of cells in a protected worksheet by following the steps below:

1. Unlock all the cells by creating a custom style and setting the **locked** method as False.
2. Separately lock the cell range you want to be read-only.

```javascript
// Configure Workbook and Worksheet
var spread = new GC.Spread.Sheets.Workbook("ss");
var sheet = spread.getActiveSheet();
// Unlock all the cells in the worksheet via the styles
let style = new GC.Spread.Sheets.Style();
style.locked = false;
// Set style as default style for all the cells in the sheet
sheet.setDefaultStyle(style);
// Separately lock the cell range you want to be read-only
new GC.Spread.Sheets.CellRange(sheet, 0, 0, 13, 4).locked(true);
// Set sheet to be protected
sheet.options.isProtected = true;
```

The **options.protectionOptions** property can be used to specify the areas which can be changed. These areas can include resizing, dragging, inserting, or deleting rows or columns, and so on.
When the **isProtected** option is set to True, the following properties will take effect:

| Property | Description |
| -------- | ----------- |
| `allowDragInsertRows` | Allows you to perform the drag operation while inserting rows. |
| `allowDragInsertColumns` | Allows you to perform the drag operation while inserting columns. |
| `allowInsertRows` | Allows you to insert rows. |
| `allowInsertColumns` | Allows you to insert columns. |
| `allowDeleteRows` | Allows you to delete rows. |
| `allowDeleteColumns` | Allows you to delete columns. |
| `allowSelectLockedCells` | Allows you to select locked cells. |
| `allowSelectUnlockedCells` | Allows you to select unlocked cells. |
| `allowSort` | Allows you to sort ranges. |
| `allowFilter` | Allows you to filter ranges. |
| `allowEditObjects` | Allows you to edit floating objects. |
| `allowResizeRows` | Allows you to resize rows. |
| `allowResizeColumns` | Allows you to resize columns. |
| `allowOutlineRows` | Allows you to expand or collapse the row groups. |
| `allowOutlineColumns` | Allows you to expand or collapse the column groups. |

When the **isProtected** option is set to false, the above protection options will not take any effect.

## Enable Protection Options in a Locked Worksheet

You can protect the worksheet and enable various protection options that are available in SpreadJS.

```javascript
var spread = new GC.Spread.Sheets.Workbook(document.getElementById("ss"));
var sheet = spread.getActiveSheet();
sheet.options.isProtected = true;
sheet.options.protectionOptions.allowDeleteRows = true;
sheet.options.protectionOptions.allowDeleteColumns = true;
sheet.options.protectionOptions.allowInsertRows = true;
sheet.options.protectionOptions.allowInsertColumns = true;
sheet.options.protectionOptions.allowDragInsertRows = true;
sheet.options.protectionOptions.allowDragInsertColumns = true;
sheet.options.protectionOptions.allowOutlineColumns = true;
```

> **Note:** The protection options: allowInsertRows, allowInsertColumns, allowDeleteRows, and allowDeleteColumns are available only when you are performing an operation on the user interface. In other words, the value will only restrict the insertion and deletion of rows and columns commands in the context menu.

## Set Alert Message for Protected Groups

By default, you cannot expand or collapse the outline row or column groups in a protected worksheet. An invalidOperation event is triggered which you can also bind to display an alert message as shown below:

```javascript
// Set alert message
spread.bind(GC.Spread.Sheets.Events.InvalidOperation, (e, args) => {
    if(args.invalidType === GC.Spread.Sheets.InvalidOperationType.groupProtected){
    args.message="Expand or Collapse operation is not allowed for a protected worksheet.";
    alert(args.message)
    }
}); 
```

## Protect Sheet with Password

You can choose to set the password while protecting the worksheet using the **protect** method. However, on invoking the protect method, the **isProtected** option will be set to true automatically.

```javascript
//Protect the worksheet 
var password = 'AddedPassword'; 
activeSheet.protect(password); 
```

You can further unprotect the worksheet by providing the password as a parameter to the **unprotect** method.

```javascript
//unprotect the worksheet with a password
if(activeSheet.hasPassword()) {
    activeSheet.unprotect(password);
} else {
    activeSheet.unprotect();
}
```

## Hide Formula in a Protected Worksheet

You can control the visibility of formula cells in a protected sheet by using either the **hidden** property of the [Style ](gcdocsite__documentlink?toc-item-id=1a4e9265-6694-48bb-b0fc-15e5ab238a26)class or the **hidden** method of the [CellRange](gcdocsite__documentlink?toc-item-id=64f05fd4-fafa-47dc-9856-b74263f357ec) class. By default, the hidden attribute is set to false, indicating that the formulas are not hidden. Additionally, it supports export and import of SSJSON, SJS, and XLSX.
The hidden attribute is useful in the cases like generating KPI data or year-end bonus based on employee self-assessment and supervisor evaluation, wherein the employer wants to hide the relevant formulas and protect the evaluation system.
The following code sample shows how to a hide cell using the **hidden** property in GC.Spread.Sheets.Style type.

```javascript
// Sets whether the cell formula is visible when the sheet is protected.
activeSheet.options.isProtected = true;

// Create a style with hidden property true
var style = new GC.Spread.Sheets.Style();
style.hidden = true;
activeSheet.setStyle(1, 1, style, GC.Spread.Sheets.SheetArea.viewport);

// Apply style to a cell containing formula
activeSheet.setFormula(1, 1, "=SUM(1,2)");
```

Alternatively, this code sample uses the **hidden** method in GC.Spread.Sheets.CellRange type.

```javascript
// Sets whether the cell formula is visible when the sheet is protected.
activeSheet.options.isProtected = true;
activeSheet.setFormula(1, 3, "=SUM(10,20)");
activeSheet.getRange(1, 3, GC.Spread.Sheets.SheetArea.viewport).hidden(true);
```

The following SpreadJS functionalities are affected by hidden attributes:

* The **Formula bar** and **Formula Editor** panel do not display any formula when the **hidden** property is set on cells.
* The default data in the **Input Editor** is empty when the hidden cell is in the edit mode.
* Hidden cells do not copy formulas, only results, but cuts always contain formulas.
    However, you can prevent this by setting the **locked** property to true.
* The **showFormulas** property does not display the formulas of hidden cells.
* **FORMULATEXT()** method cannot get the cells’ formula if the hidden property has taken effect.

Note that the **hidden** and **locked** properties mutually influence each other’s functionality as explained in the given table:

| Case | locked | hidden | Result |
| ---- | ------ | ------ | ------ |
| Sheet is not protected | True/False | True/False | Both locked and hidden do not take effect. |
| @rows=4:Sheet is protected | False | False | The cell can be edited, and the formula is displayed normally. |
| True | False | The cell is locked and cannot be edited, but the formula is displayed normally. |
| False | True | The cell can be edited, but the formula is hidden. <br>In the edit mode, the input box shows a null as the default value. |
| True | True | The cell is locked and cannot be edited, and the formula is hidden. |

**Limitations**

* TableSheet, GanttSheet, and ReportSheet do not support hidden attributes.
* Hidden attributes do not affect the formulas accessed through the APIs.

## Using Designer

To access the Protect Sheet dialog, navigate to the Protect Sheet option by right-clicking on the sheet name displayed on the Tab strip.
**Steps to protect and unprotect the worksheet using Protect Sheet Dialog**

1. Enter the password to protect the worksheet and check/ uncheck multiple options from the available list of options in the Protect Sheet dialog box.
<br>
    ![protect-sheet-dialog](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/protect-sheet-dialog.e50889.png)
<br>
2. When you enter the password to protect the worksheet, another dialog confirms the password.
<br>
    ![confirm-protect](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/confirm-protect.fa2578.png)

Once a password is successfully set, you can access the protected worksheet, but cannot make any changes to the sheet. To unprotect the worksheet, enter the set password using the Unprotect Sheet dialog.
![unprotect-sheet](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/unprotect-sheet.bb9b1b.png?width=301&verticalAlign=baseline)