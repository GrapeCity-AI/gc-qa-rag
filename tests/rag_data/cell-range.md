# Cell Range

A tutorial showing how to work with cell ranges in SpreadJS, including getting the range by the row/column index, range address, or data type

## Content

SpreadJS provides an easy way to access a range of cells in the sheet area. You can conveniently get the range information in the sheet using the [getRange](gcdocsite__documentlink?toc-item-id=995f2b70-17d8-47a4-8e09-962f84b4dfc1#getRange) method.
It allows users to conveniently choose which way to obtain range information in the sheet area according to their requirements, either through row and column index or via range address. This is covered in the following two sections.

## Get Range by Row and Column Index

You can get a series of cells in a range of sheet areas using the **getRange(row, col, rowCount, colCount, sheetArea)** method. This method uses parameters such as row index, column index, row count of range, and column count. In this manner, you get a range of cells by row index and column index in the specified sheet area.
The following image displays an example of getting cell range by row and column index.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/row-and-column-info.png)

The following code snippet depicts how to use the **getRange** method to specify range B2:F6 with row and column index.

```javascript
$(document).ready(function () {
    // Initializing Spread
    var spread = new GC.Spread.Sheets.Workbook(document.getElementById('ss'), { sheetCount: 1 });
    // Get the activesheet
    var sheet = spread.getActiveSheet();

    // Get range by row and column info
    var range = sheet.getRange(1, 1, 5, 5, GC.Spread.Sheets.SheetArea.viewport);
    range.text("Text");
});
```

## Get Range by Range Address

You can also get a range of cells in the sheet area using the **getRange(address, sheetArea)** method. This method gets a range of cells in the specified sheet area using a range address string.
The following image displays an example of getting cell range by range address.

![](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/8d606653-16a0-474d-b9dc-e2b4d01c2446/images/range-address.png)

The following code snippet depicts how to use the **getRange** method to specify range A1:E5 with range address string.

```javascript
$(document).ready(function () {
    // Initializing Spread
    var spread = new GC.Spread.Sheets.Workbook(document.getElementById('ss'), { sheetCount: 1 });
    // Get the activesheet
    var sheet = spread.getActiveSheet();

    // Get range by range address
    var range = sheet.getRange('A1:E5', GC.Spread.Sheets.SheetArea.viewport);
    range.text("Text");
});
```

## Get Range by Type of Data

You can get a range of cells based on the type of data available in the sheet using the [getUsedRange](gcdocsite__documentlink?toc-item-id=995f2b70-17d8-47a4-8e09-962f84b4dfc1#getUsedRange) method. It quickly obtains the maximum range of different types of data using the enumeration option [UsedRangeType](gcdocsite__documentlink?toc-item-id=eb475f3d-17fd-4aa5-8921-6731663e66a4) as a parameter. Each UsedRangeType enum value focuses on a specific aspect of worksheet range which further helps to obtain different data ranges quickly throughout a worksheet when you are working with different forms of data such as sparklines, charts, slicers, tags, all and so on.
The table below illustrates different members of UsedRangeType enumeration with their description.

| **Member Name** | **Description** |
| ----------- | ----------- |
| all | Includes all types of content in the used range such as data, formulas, tags, styles, sparklines, charts and more |
| axis | Includes cells referenced by charts for their axis |
| chart | Includes data ranges used for plotting chart series |
| colstyle | Includes columns that have specific styles applied, even if it does not contain data |
| comment | Includes cells that contain comments |
| conditionFormat | Includes cells with conditional formatting rules applied |
| data | Includes cells that contain data such as text, numbers or dates |
| dataRange | Includes ranges used as data sources for tables or charts |
| dataValidation | Includes cells with data validation rules applied |
| filter | Includes cells involved in filter operations such as the header row for a table with a filter |
| formula | Includes cell containing formulas |
| picture | Includes cells associated with images or pictures added to the sheet |
| pivottable | Includes cell associated with pivot tables, including data sources and calculated fields |
| rowStyle | Includes rows that have specific styles applied |
| shape | Includes cells with shapes or drawings |
| slicer | Includes cells related to slicers connected to tables or pivot tables |
| span | Includes cells in merged ranges |
| sparkLine | Includes cells containing sparklines |
| style | Includes cells with specific styles applied |
| table | Includes cells that are part of table |
| tag | Includes cells with associated tags |

The following example code demonstrates how to retrieve the cell range with cell tags applied. However, you can use any of the UsedRangeType enum members described above to retrieve the cell range as per your requirement.

```javascript
function getRangeStyle() {
    var sheet = spread.getSheet(0);
    var styleRange = sheet.getUsedRange(GC.Spread.Sheets.UsedRangeType.style);
    //  styleRange:{row: 2, col: 2, rowCount: 3, colCount: 3}

    sheet.setSelection(styleRange.row, styleRange.col, styleRange.rowCount, styleRange.colCount, GC.Spread.Sheets.SheetArea.viewport, GC.Spread.Sheets.StorageType.style);
}

function getRangeTag() {
 var sheet = spread.getSheet(0);
 sheet.setTag(2, 2, "value");
 sheet.setTag(4, 2, new Date());
 sheet.setTag(6, 8, { Product: 'SpreadJS', Price: 99999 });

 var usedRangeTag = sheet.getUsedRange(GC.Spread.Sheets.UsedRangeType.tag);
 console.log(usedRangeTag); // usedRangeTag:{row: 2, rowCount: 5, col: 2, colCount: 7}
}
```