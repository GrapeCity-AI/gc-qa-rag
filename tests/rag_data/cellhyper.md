# Hyperlink Cell

A tutorial showing how to work with hyperlink cell types in SpreadJS, including callback actions

## Content

You can use a hyperlink cell to contain text that functions as a single hyperlink. The hyperlink cell type lets you set the color of the hyperlink as well as the color after the link has been accessed. You can also display text in the cell that is different from the hyperlink and set a tooltip to show when the mouse pointer hovers over the hyperlink.
When you click the link, it opens a new page and navigates to the link URL.

![cellhyperlink](/DOCUMENT_SITE_LINK_PREFIX_HERE/document-site-files/images/ef9b66d1-0ae2-4e94-b8cb-f9f893aacc8d/cellhyperlink.7b242c.png)

The following code sample creates a hyperlink cell type.

```javascript
var cellType = new GC.Spread.Sheets.CellTypes.HyperLink();
cellType.linkColor("blue");
cellType.visitedLinkColor("#FF2235");
cellType.text("Hyperlink");
cellType.linkToolTip("Click here");
activeSheet.getCell(1, 1).cellType(cellType).value("https://developer.mescius.com/");
activeSheet.getRange(1, -1, 1, -1).height(30);
```

## Handle Callback Action

You can execute callback actions on a hyperlink cell using the [onClickAction](gcdocsite__documentlink?toc-item-id=f385951c-a3e5-4b3b-b328-c9b194cadbe5#onClickAction) method in the **HyperLink** class.
The following code sample sets a callback action to the hyperlink where it will be executed when the hyperlink is clicked by a user. The action changes the sheet name to "Hyperlink" and the sheet tab color to red.

```javascript
var h = new GC.Spread.Sheets.CellTypes.HyperLink();
sheet.setCellType(3, 2, h, GC.Spread.Sheets.SheetArea.viewport);
h.text('Spread.Sheets Site');
h.linkColor('blue');
// Set a callback action to the hyperlink
h.onClickAction(function () {
   var setSheetTabColor = {
      canUndo: true,
      execute: function (context, options, isUndo) {
      sheet.name('Hyperlink');
      sheet.options.sheetTabColor = 'red';
      }
   };
   var commandManager = spread.commandManager();
   var commandName = 'setSheetTabStyle';
   
// code to register this callback to the commandManager
   commandManager.register(commandName, setSheetTabColor, null, false, false, false, false);
   commandManager.execute({cmd: commandName});
});
```

You can also control whether the active cell should be moved to the hyperlink cell when the hyperlink is clicked by a user using the [activeOnClick](gcdocsite__documentlink?toc-item-id=f385951c-a3e5-4b3b-b328-c9b194cadbe5#activeOnClick) method in the **HyperLink** class.
The following code can be used to get and set whether to move to the active cell when the hyperlink is clicked.

```javascript
h.activeOnClick(true);
```