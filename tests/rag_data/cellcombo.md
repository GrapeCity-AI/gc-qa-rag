# Combo Box Cell

A tutorial showing how to work with Combo Box cell types in SpreadJS, including a explanation of how to set the position

## Content

SpreadJS provides the support for a combo box cell which displays a drop-down list.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/cellcombo.png)

If the item width is less than the cell width, then the item width is set to the cell width; otherwise, the item width is equal to the width of the longest item.

The following example creates a combo box cell with a list of items.

```javascript
var cellType2 = new GC.Spread.Sheets.CellTypes.ComboBox();
cellType2.items(["a","b","c"]);
activeSheet.getCell(2, 2).cellType(cellType2);
```

The combo cell is editable and you can type in the edit portion of the cell and the matching item in the list to select it automatically.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/cellecombo.png)

The following example creates an editable combo box cell with a list of items.

```javascript
var items2 = ["a", "ab", "abc", "apple", "boy", "cat", "dog"];
var eComboBoxCellType = new GC.Spread.Sheets.CellTypes.ComboBox().items(items2).editable(true);
activeSheet.getCell(1, 3).cellType(eComboBoxCellType);
activeSheet.setColumnWidth(3,120);
```

The maximum number of visible items in the drop-down list is 20. Use the up or down arrow keys to select items when the drop-down list is displayed. The left and right arrow keys commit the selected item and move to the next or previous cell. The Enter key also commits the selected item and the Esc key cancels the selected item.
The arrow keys may not behave the same when using rapid input mode. If the cell's editor status is EditorStatus.Enter, pressing the left or right arrow key ends editing and navigates to the previous or next cell. If the editor status is EditorStatus.Edit, pressing the left or right arrow key does not end editing.

### **Binding ComboBox Cell**

SpreadJS allows users to create dynamic dropdown lists in spreadsheet cells by binding the ComboBox to a data source, such as a table name or a formula evaluation result. Users can use formulas to filter, get unique values, or sort the data source. To bind the ComboBox cell type, use the `dataBinding` method of the `ComboBoxCellType` class which accepts dataSource, text, and value properties.

* The “text” or “value” must be a column name of the table or a column index of the formula evaluation result.
* If either of the options, “text“ or “value“ is set, the other one will take the same value.
* If neither “text“ nor “value“ are set, both “text“ and “value“ will bind to the first column of the data source.

> Note-
>
> * To use data binding in a `ComboBoxCellType`, the option `spread.options.allowDynamicArray` must be enabled.
> * The `dataBinding` method does not affect the `editValueType` of the `ComboBoxCellType`.
> * If the dataSource is a formula, the result of the formula must be an array.
> * When copying/moving/renaming the worksheet, the formula referenced range will not auto change.
> * It doesn’t support R1C1 reference in the formula.

The following code is used to bind **ComboBox** cell types with a table column using the table name as the dataSource and with formula evaluation result as dataSource.

```javascript
spread.options.allowDynamicArray = true;
const dataManager = spread.dataManager();
const productsTable = dataManager.addTable("Products", {
     remote: {
         read: {
             url: 'https://northwind.vercel.app/api/products'
         }
     }
 });
await productsTable.fetch(true);

// Binding to a table name
let sheet = spread.getSheet(0);
sheet.name("Binding To A Table Name");
sheet.setColumnWidth(2, 250);
let binding = { dataSource: "Products", text: "name", value: "id" };
let cellType = new GC.Spread.Sheets.CellTypes.ComboBox();
cellType.dataBinding(binding);
sheet.getCell(2, 2).cellType(cellType);

// Binding to a formula query
let sheet1 = spread.getSheet(1);
sheet1.name("Binding To A Formula Query");
sheet1.setColumnWidth(2, 250);
let binding1 = { dataSource: '=SORT(UNIQUE(QUERY("Products", {"name","id"})))', text: 0, value: 1 };
let cellType1 = new GC.Spread.Sheets.CellTypes.ComboBox();
cellType1.dataBinding(binding1);
sheet1.getCell(2, 2).cellType(cellType1);
```

### **Setting Dropdown Position**

SpreadJS ComboBox cell type provides **allowFloat** property which handles the dropdown positioning of combobox. It helps in managing the dropdown position and size when the SpreadJS component does not have sufficient space to fit the dropdown or to prevent the dropdown from overflowing.
When **allowFloat** property is set to false and there isn’t enough space in SpreadJS to contain the dropdown, then the ComboBox cell type resizes the dropdown to ensure it does not overflow the area of the SpreadJS instance.
However, if the **allowFloat** property is set to true (default), then on opening the dropdown box, it floats above the SpreadJS area to show more content and it does not affect the size and position of the dropdown box when the user scrolls the SpreadJS.
The following images display the ComboBox cell type with the **allowFloat** property.

| **allowFloat = false** | **allowFloat = true** |
| :----------------: | :---------------: |
| ![allowfloat-false](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/allowfloat-false.960bb8.png) | ![allowfloat-true](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/df1fe1ee-eb3c-4da7-8c20-a0d8d2b7e734/allowfloat-true.030f94.png) |
