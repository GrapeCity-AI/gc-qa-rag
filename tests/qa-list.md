### Q1: 如何创建一个动态的“相机”视图, 让它显示的区域可以根据另一个单元格的输入值（例如"A1:C5"或"D1:F10"）自动更新？

**A:** 你可以通过创建一个相机形状（Camera Shape），并将其“公式”属性与一个包含范围地址的单元格链接起来。当该单元格的文本更新时，相机形状所展示的实时视图也会随之改变。

```javascript
// 假设 spread 是你的工作簿实例, activeSheet 是当前工作表
// B1单元格用于输入你想要查看的范围, 例如 "A1:C5"
let sourceCell = activeSheet.getCell(0, 1); // B1
sourceCell.text("A1:C5");

// 创建一个相机形状
let cameraShape = activeSheet.shapes.addCameraShape("dynamicCamera", "=INDIRECT(B1)", 100, 100, 200, 150);

// 当B1单元格内容改变时, 相机形状会自动更新其显示的区域
// 例如, 将B1的内容改为 "D1:F10", cameraShape就会显示D1:F10的内容
```
**参考文档:** `camerashape.md`, `cellreferences.md`

---
### Q2: 我能否在单元格中放置一个按钮，点击该按钮后，它会获取相邻单元格（例如左侧单元格）的数值，进行一个数学运算（如乘以2），然后将结果输出到右侧的单元格？

**A:** 可以。你需要定义一个按钮类型的单元格（CellButton），并为其命令（command）绑定一个自定义函数。这个函数可以访问工作表上下文，读取任意单元格的值，执行计算，并将结果写入目标单元格。

```javascript
// 假设 spread 是你的工作簿实例, activeSheet 是当前工作表
// 在 B2 单元格创建一个按钮
let buttonCell = activeSheet.getCell(1, 1); // B2
buttonCell.cellType(new GC.Spread.Sheets.CellTypes.Button().text("Calculate"));

// 定义一个自定义命令
spread.commandManager().register("calculateNeighbor", {
    canUndo: true,
    execute: function (context, options, isUndo) {
        const sheet = context.getActiveSheet();
        const { row, col } = options.activeCell;
        const leftValue = sheet.getValue(row, col - 1);
        if (typeof leftValue === 'number') {
            const result = leftValue * 2;
            sheet.setValue(row, col + 1, result);
        } else {
            sheet.setValue(row, col + 1, "Error: Not a number");
        }
    }
});

// 将命令绑定到按钮单元格
activeSheet.getCell(1, 1).command("calculateNeighbor");
```
**参考文档:** `cellbutton.md`, `calculate-function.md`

---
### Q3: 如果我想让单元格内的文本距离上下边框各10像素，距离左右边框各5像素，应该如何设置cell padding？

**A:** 你可以使用 `padding` 样式属性来实现。这个属性接受一个类似CSS padding的字符串，顺序为 "上 右 下 左"。

```javascript
// 假设 cell 是你要操作的单元格实例
cell.style(new GC.Spread.Sheets.Style().padding("10 5 10 5"));

// 或者分别设置
cell.style(new GC.Spread.Sheets.Style().paddingTop(10).paddingRight(5).paddingBottom(10).paddingLeft(5));
```
**参考文档:** `cellpadding.md`

---
### Q4: 如何实现一个级联下拉列表，即B1单元格的下拉选项依赖于A1单元格所选的值？例如，当A1选“水果”时，B1的选项是“苹果、香蕉”，当A1选“蔬菜”时，B1的选项是“菠菜、胡萝卜”。

**A:** 你需要为A1单元格设置一个下拉列表。然后，监听`ValueChanged`事件。当A1的值改变时，根据新值动态地为B1单元格创建一个新的下拉列表。

```javascript
// 假设 activeSheet 是当前工作表
// 设置A1的下拉列表
let cellA1 = activeSheet.getCell(0, 0);
cellA1.cellType(new GC.Spread.Sheets.CellTypes.ComboBox().items(["Fruit", "Vegetable"]));

// 定义数据源
const options = {
    "Fruit": ["Apple", "Banana"],
    "Vegetable": ["Spinach", "Carrot"]
};

// 监听值变化事件
spread.getActiveSheet().bind(GC.Spread.Sheets.Events.ValueChanged, function (e, args) {
    if (args.row === 0 && args.col === 0) {
        let value = args.newValue;
        let cellB1 = activeSheet.getCell(0, 1);
        if (options[value]) {
            cellB1.cellType(new GC.Spread.Sheets.CellTypes.ComboBox().items(options[value]));
            cellB1.value(""); // 清空B1的值
        }
    }
});
```
**参考文档:** `cell-dropdowns.md`, `cellcombo.md`

---
### Q5: 我创建了一个自定义函数 `MYFUNC`, 我希望当这个函数计算出错时（例如返回 #ERROR!），单元格的背景色能自动变为红色。这能实现吗？

**A:** 可以，这需要结合使用自定义函数和条件格式化（Conditional Formatting）。首先定义你的自定义函数，然后在单元格上设置一个条件格式规则，规则检查单元格是否为错误值 (`ISERROR`)，如果是，则应用红色背景样式。

```javascript
// 1. 定义自定义函数
function MyFunc(arg) {
    if (typeof arg !== 'number') {
        throw new GC.Spread.Sheets.Calc.CalcError("#ERROR!");
    }
    return arg * 10;
}
spread.addCustomFunction("MYFUNC", MyFunc, { name: "MYFUNC", description: "My custom function", parameters: [{ name: "arg" }] });

// 2. 在A1单元格使用函数
activeSheet.getCell(0, 0).formula('=MYFUNC(B1)');

// 3. 为A1设置条件格式
let style = new GC.Spread.Sheets.Style();
style.backColor = "red";
let rule = new GC.Spread.Sheets.ConditionalFormatting.FormulaRule();
rule.formula("=ISERROR(A1)");
rule.style(style);
activeSheet.conditionalFormats.addRule(rule, [new GC.Spread.Sheets.Range(0, 0, 1, 1)]);
```
**参考文档:** `calculate-function.md`, `cell-states.md`, `cell-style.md`

---
### Q6: 我需要将一个数字显示为带有千位分隔符、保留两位小数且后缀为“USD”的格式，例如 `12345.678` 显示为 `12,345.68 USD`。对应的格式化字符串应该是什么？

**A:** 你应该使用格式化字符串 `#,##0.00 "USD"`。

```javascript
// 假设 cell 是你要操作的单元格实例
cell.formatter('#,##0.00 "USD"');
cell.value(12345.678); // 单元格将显示 "12,345.68 USD"
```
**参考文档:** `cellformat.md`

---
### Q7: 如何实现当A1单元格的值大于100时，自动锁定B1单元格，使其不可编辑？

**A:** 这需要结合数据验证（Data Validation）和单元格锁定（Cell Lock）。你可以为A1设置一个数据验证规则，当值不满足条件时显示提示。然后通过监听`ValueChanged`事件，在A1的值大于100时，设置B1单元格的样式 `locked` 属性为 `true` 并保护工作表。

```javascript
// 保护工作表，但允许选择未锁定的单元格
activeSheet.options.protectionOptions.selectUnlockedCells = true;
activeSheet.options.isProtected = true;

// 默认解锁B1
let cellB1 = activeSheet.getCell(0, 1);
let style = cellB1.style();
style.locked = false;
cellB1.style(style);

// 监听A1的值变化
activeSheet.bind(GC.Spread.Sheets.Events.ValueChanged, function (e, args) {
    if (args.row === 0 && args.col === 0) {
        let value = args.newValue;
        let cellB1 = activeSheet.getCell(0, 1);
        let style = cellB1.style();
        style.locked = (value > 100); // 如果A1 > 100, 则锁定B1
        cellB1.style(style);
    }
});
```
**参考文档:** `celllock.md`, `cellvaluerule.md`

---
### Q8: 我想在'Sheet1'的A1单元格中，计算'Sheet2'上A1到A10单元格的总和。公式应该怎么写？

**A:** 公式应该使用带有工作表名称的单元格引用：`=SUM(Sheet2!A1:A10)`。

```javascript
// 假设 spread 有 'Sheet1' 和 'Sheet2'
let sheet1 = spread.getSheetFromName('Sheet1');
let sheet2 = spread.getSheetFromName('Sheet2');

// 在 Sheet2 中填充数据
for (let i = 0; i < 10; i++) {
    sheet2.setValue(i, 0, i + 1); // A1:A10 分别为 1 到 10
}

// 在 Sheet1 的 A1 中设置公式
sheet1.getCell(0, 0).formula('=SUM(Sheet2!A1:A10)');

// Sheet1 的 A1 将显示 55
```
**参考文档:** `cellreferences.md`

---
### Q9: 如果我将A1到C3的区域合并成一个大的单元格，然后在这个合并的单元格中输入很长的文本，文本会自动换行吗？如果想让它在垂直方向上居中对齐，该怎么做？

**A:** 合并单元格后，你需要手动开启`wordWrap`样式才能使文本自动换行。同时，可以通过设置`vAlign`为`center`来实现垂直居中。

```javascript
// 假设 activeSheet 是当前工作表
// 合并 A1:C3
activeSheet.addSpan(0, 0, 3, 3);

let cell = activeSheet.getCell(0, 0); // 获取合并区域的左上角单元格
cell.value("This is a very long text that should wrap inside the merged cell.");

// 创建样式并应用
let style = new GC.Spread.Sheets.Style();
style.wordWrap = true;
style.vAlign = GC.Spread.Sheets.VerticalAlign.center;
style.hAlign = GC.Spread.Sheets.HorizontalAlign.center; // 水平也居中
cell.style(style);
```
**参考文档:** `cellspan.md`, `celloverflow.md`, `cellalign.md`

---
### Q10: 我能否创建一个单元格，它既是一个下拉列表，又带有一个复选框？

**A:** 标准的单元格类型（CellTypes）不支持将下拉列表和复选框直接混合在同一个单元格中。你需要创建一个自定义单元格类型（Custom Cell Type）来实现这种复杂的交互行为。这是一个高级用例，需要自己编写绘制和事件处理逻辑。或者，你可以采用变通方法，例如在相邻的两个单元格中分别设置复选框和下拉列表。
**参考文档:** `celltypes.md`, `cellcustom.md`, `cellcheckbox.md`, `cell-dropdowns.md`

---
### Q11: 如何设置一个数据验证规则，要求单元格A1只能输入能被10整除的数字，如果输入了33，则自动向上取整为40？

**A:** 这需要结合数据验证和`ValueChanged`事件。数据验证本身不能自动修改值，但可以提示错误。自动修改值的功能需要在`ValueChanged`事件中，使用`CEILING.MATH`函数逻辑来实现。

```javascript
// 假设 activeSheet 是当前工作表
let cell = activeSheet.getCell(0, 0);

// 监听值变化
activeSheet.bind(GC.Spread.Sheets.Events.ValueChanged, function (e, args) {
    if (args.row === 0 && args.col === 0) {
        let value = args.newValue;
        if (typeof value === 'number' && value % 10 !== 0) {
            // 使用CEILING.MATH逻辑，第二个参数是基数
            let correctedValue = Math.ceil(value / 10) * 10;
            // 使用setTimeout防止事件冲突，并更新单元格值
            setTimeout(() => {
                activeSheet.setValue(args.row, args.col, correctedValue);
            }, 0);
        }
    }
});
```
**参考文档:** `cellvaluerule.md`, `ceiling.math.md`

---
### Q12: 如果我尝试将一个包含0或负数值的图表数据系列的垂直轴设置为对数刻度，会发生什么？

**A:** 将包含0或负数的轴设置为对数刻度会导致错误或未定义的行为，因为0和负数没有对数。图表库通常会忽略这些数据点，或者直接无法渲染该轴，甚至可能抛出错误。在设置对数刻度前，必须确保所有数据点都大于0。
**参考文档:** `change-vertical-axis-to-logarithmic-scale.md`

---
### Q13: 我在使用级联瀑布图（Cascade Sparkline），如何让正值显示为绿色，负值显示为红色？

**A:** 你可以在创建级联瀑布图时，通过设置其样式选项来指定不同值的颜色。

```javascript
// 假设 activeSheet 是当前工作表
let data = [10, -5, 8, -3, 12]; // 示例数据
let setting = new GC.Spread.Sheets.Sparklines.CascadeSparklineSetting();
setting.colorPositive(true, "green"); // 显示正值颜色
setting.colorNegative(true, "red");   // 显示负值颜色

activeSheet.setSparkline(0, 0, new GC.Spread.Sheets.Range(-1, -1, 1, data.length), data, GC.Spread.Sheets.Sparklines.DataOrientation.Horizontal, GC.Spread.Sheets.Sparklines.SparklineType.cascade, setting);
```
**参考文档:** `cascadesparkline.md`, `cell-style.md`

---
### Q14: 我的工作表中存在一个循环引用（例如A1依赖B1，B1依赖A1）。如果我想让它们通过几次迭代计算来收敛到一个稳定值，应该如何设置？

**A:** 你需要在工作簿的计算选项中开启迭代计算（Iterative Calculation），并设置最大迭代次数和最小变化阈值。

```javascript
// 假设 spread 是你的工作簿实例
let options = spread.options;
options.allowIterativeCalculation = true; // 开启迭代计算
options.iterativeCalculationMaximumIterations = 100; // 最大迭代100次
options.iterativeCalculationMaximumChange = 0.001; // 变化小于0.001时停止

// 在A1和B1中设置循环公式
// A1: =IF(B1="", 1, B1*0.5)
// B1: =A1+1
```
**参考文档:** `calculating-iterative.md`, `calculation-mode.md`

---
### Q15: 如何让一个单元格下拉列表的选项，动态地来自于另一个（可能隐藏的）工作表的某个范围？

**A:** 你可以使用`Range`对象作为下拉列表的`items`源，并在范围地址中指定工作表名称。

```javascript
// 假设 spread 有 'Sheet1' 和 'DataSourceSheet'
let dataSourceSheet = spread.getSheetFromName('DataSourceSheet');
// 在数据源工作表中填充数据
dataSourceSheet.setValue(0, 0, "Apple");
dataSourceSheet.setValue(1, 0, "Banana");
dataSourceSheet.setValue(2, 0, "Cherry");

// 在Sheet1的A1单元格创建下拉列表
let mainSheet = spread.getSheetFromName('Sheet1');
let cell = mainSheet.getCell(0, 0);
let list = new GC.Spread.Sheets.CellTypes.ComboBox();
// 引用另一个工作表的范围
list.items(new GC.Spread.Sheets.Range(0, 0, 3, 1), dataSourceSheet);
cell.cellType(list);
```
**参考文档:** `cell-dropdowns.md`, `cellreferences.md`, `cell-range.md`

---
### Q16: 当一个单元格的水平对齐方式设为`right`，并且文本内容超出了单元格宽度时，文本会向哪个方向溢出？

**A:** 文本溢出（Overflow）的行为通常是向右延伸，覆盖相邻的空单元格。水平对齐（`hAlign`）属性仅影响单元格内部的文本位置，而不改变溢出的方向。即使设置为`right`，溢出部分仍然会向右侧显示。
**参考文档:** `celloverflow.md`, `cellalign.md`

---
### Q17: 我想用A1单元格的复选框（Checkbox）来控制A2:C2这个范围的背景颜色。选中时为灰色，未选中时为白色。如何实现？

**A:** 你需要为A1设置一个复选框单元格类型，然后监听`ValueChanged`事件。当A1的值（true/false）改变时，获取A2:C2的范围并更新它们的`backColor`样式。

```javascript
// 假设 activeSheet 是当前工作表
// 在A1设置复选框
activeSheet.getCell(0, 0).cellType(new GC.Spread.Sheets.CellTypes.CheckBox());

// 监听值变化
activeSheet.bind(GC.Spread.Sheets.Events.ValueChanged, function (e, args) {
    if (args.row === 0 && args.col === 0) {
        let isChecked = args.newValue;
        let rangeToStyle = activeSheet.getRange(1, 0, 1, 3); // A2:C2
        rangeToStyle.backColor(isChecked ? "lightgray" : "white");
    }
});
```
**参考文档:** `cellcheckbox.md`, `cell-style.md`, `cell-range.md`

---
### Q18: 如何创建一个动态超链接，它的URL地址由多个单元格的内容拼接而成？例如，A1是"http://example.com/", B1是"search", C1是"query=gemini"，最终链接到"http://example.com/search?query=gemini"。

**A:** 你可以使用`HYPERLINK`函数，并利用`CONCATENATE`或`&`操作符来拼接字符串，生成最终的URL。

```javascript
// 假设 activeSheet 是当前工作表
activeSheet.setValue(0, 0, "http://example.com/"); // A1
activeSheet.setValue(0, 1, "search");             // B1
activeSheet.setValue(0, 2, "query=gemini");       // C1

// 在D1单元格创建超链接
let cellD1 = activeSheet.getCell(0, 3); // D1
cellD1.formula('=HYPERLINK(A1 & B1 & "?" & C1, "Click Me")');
```
**参考文档:** `cellhyper.md`, `cellreferences.md`

---
### Q19: 除了手动选择，我能否通过代码基于特定条件（例如，A列中所有包含"Total"字样的单元格）来创建一个动态的命名范围（Named Range）？

**A:** 可以。你需要遍历A列，找到所有满足条件的单元格，收集它们的地址，然后使用这些地址创建一个不连续的范围，并将其添加为命名范围。这通常需要自定义代码逻辑，而不是单一的内置函数。

```javascript
// 假设 activeSheet 是当前工作表
let ranges = [];
for (let i = 0; i < activeSheet.getRowCount(); i++) {
    let cell = activeSheet.getCell(i, 0);
    let text = cell.text();
    if (text && text.includes("Total")) {
        ranges.push(new GC.Spread.Sheets.Range(i, 0, 1, 1));
    }
}
// 使用找到的范围数组创建一个命名范围
if (ranges.length > 0) {
    spread.addNamedStyle(new GC.Spread.Sheets.Style("totalCellsStyle", "red"), ranges);
}
```
**参考文档:** `cell-range.md`, `cells.md`

---
### Q20: 如果我用相机形状（Camera Shape）引用了一个应用了条件格式的区域，当源区域的颜色因数值变化而改变时，相机形状里的视图颜色会同步更新吗？

**A:** 会。相机形状提供的是一个源区域的实时“快照”，它不仅包括单元格的值，也包括它们的样式和格式。因此，当源区域的条件格式被触发，导致背景色、字体色等发生变化时，相机形状中的视图会实时、同步地反映这些视觉上的变化。
**参考文档:** `camerashape.md`, `cell-style.md`

---
### Q21: `CEILING.PRECISE` 和 `CEILING` 函数在处理负数时有何关键区别？

**A:** 主要区别在于取整方向。对于负数，`CEILING`函数会向“更接近0”的方向取整（例如 `CEILING(-1.2, -1)` 结果是-1），而`CEILING.PRECISE`会向“远离0”的方向取整（例如 `CEILING.PRECISE(-1.2, -1)` 结果是-2）。在需要严格遵守向正无穷大方向舍入的数学或工程计算中，`CEILING.PRECISE`更为可靠。
**参考文档:** `ceiling.precise.md`, `ceiling.md`, `ceiling.math.md`

---
### Q22: 我能否在单元格里放一个按钮，点击后触发一个HTTP GET请求去获取外部数据，并把返回结果填充到下面的单元格里？

**A:** 可以。这需要结合单元格按钮和自定义命令。在自定义命令的`execute`方法中，你可以使用`fetch` API来执行网络请求，并在Promise成功后将数据写入到指定的单元格中。

```javascript
// 定义一个获取数据的命令
spread.commandManager().register("fetchData", {
    canUndo: false, // 网络请求通常不可撤销
    execute: function (context, options, isUndo) {
        const sheet = context.getActiveSheet();
        const { row, col } = options.activeCell;
        
        fetch('https://api.example.com/data')
            .then(response => response.json())
            .then(data => {
                // 将获取到的数据填充到按钮下方的单元格
                sheet.setValue(row + 1, col, JSON.stringify(data));
            })
            .catch(error => {
                sheet.setValue(row + 1, col, "Failed to fetch data");
            });
    }
});

// 在A1单元格设置按钮并绑定命令
activeSheet.getCell(0, 0).cellType(new GC.Spread.Sheets.CellTypes.Button().text("Fetch Data"));
activeSheet.getCell(0, 0).command("fetchData");
```
**参考文档:** `cellbutton.md`

---
### Q23: 如何创建一个带有自动完成（auto-complete）功能的组合框（ComboBox）单元格？

**A:** `ComboBox`单元格类型默认就支持自动完成。当你开始输入时，它会自动筛选下拉列表中的项目，并显示匹配的选项。你只需确保为它提供了`items`列表。

```javascript
let states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", ...];
let combo = new GC.Spread.Sheets.CellTypes.ComboBox().items(states);
activeSheet.getCell(0, 0).cellType(combo);
// 当用户在单元格中输入 "Ala" 时，下拉列表会自动筛选出 "Alabama" 和 "Alaska"
```
**参考文档:** `cellcombo.md`

---
### Q24: 我想创建一个自定义单元格类型，外观像一个滑块（Slider），拖动滑块可以改变单元格的数值（0-100）。这该如何实现？

**A:** 你需要继承`GC.Spread.Sheets.CellTypes.Base`，并重写它的核心方法：`paint`方法用于绘制HTML滑块元素，`getHitInfo`和`processMouseDown`等方法用于处理鼠标交互，`getEditorValue`和`setEditorValue`用于同步滑块值和单元格值。这是一个高级功能，需要深入理解其API。
**参考文档:** `cellcustom.md`, `celltypes.md`

---
### Q25: 如何实现当用户在一个单元格中输入有效值后，该单元格立即被锁定，防止再次修改？

**A:** 你可以监听`CellEditEnded`事件。在这个事件的处理函数中，检查输入的值是否有效。如果有效，则获取该单元格的样式，设置`locked`为`true`，并重新应用样式。前提是工作表需要预先被保护。

```javascript
// 保护工作表
activeSheet.options.isProtected = true;

// 监听编辑结束事件
activeSheet.bind(GC.Spread.Sheets.Events.CellEditEnded, function (e, args) {
    const { row, col, editingText } = args;
    // 假设“有效”意味着不为空
    if (editingText) {
        let cell = activeSheet.getCell(row, col);
        let style = cell.style() || new GC.Spread.Sheets.Style();
        style.locked = true;
        cell.style(style);
    }
});
```
**参考文档:** `celllock.md`, `cellvaluerule.md`

---
### Q26: 单元格的内边距（padding）和对齐（alignment）是如何相互作用的？如果我设置了左内边距为20px，同时又设置了水平居中对齐，文本会显示在哪里？

**A:** 内边距（padding）会首先在单元格的内部边界创建一块空白区域。然后，对齐（alignment）属性会在“除去内边距后”的剩余空间内进行工作。因此，如果你设置了20px的左内边距和水平居中，文本将会在“从左侧第20个像素点开始到右侧边框”这个区域内居中显示，而不是在整个单元格的绝对中心。
**参考文档:** `cellpadding.md`, `cellalign.md`

---
### Q27: 如何用代码高效地遍历当前工作表A列的所有单元格，并将它们的值拼接成一个用逗号分隔的字符串？

**A:** 你应该使用`getRange`获取整个A列的范围，然后用`getValues`一次性将所有值读入一个数组中。在数组中处理数据远比逐个单元格读取要快得多。

```javascript
// 假设 activeSheet 是当前工作表
let rowCount = activeSheet.getRowCount();
// 获取A列的所有值
let columnValues = activeSheet.getRange(0, 0, rowCount, 1).values();

// 使用 a.flat().filter(v => v != null).join(',') 来处理数组
let resultString = columnValues.flat().filter(v => v != null).join(',');
```
**参考文档:** `cells.md`, `cell-range.md`

---
### Q28: 当我合并(span)了A1:B2四个单元格后，如果我只给这个合并后的大单元格设置一个底部边框（bottom border），边框会出现在哪里？

**A:** 边框会应用到整个合并区域的底部，即在第二行的下方，从A列延伸到B列。它表现得就像一个独立的大单元格一样。

```javascript
// 假设 activeSheet 是当前工作表
activeSheet.addSpan(0, 0, 2, 2); // 合并 A1:B2
let cell = activeSheet.getCell(0, 0);
let border = new GC.Spread.Sheets.LineBorder("black", GC.Spread.Sheets.LineStyle.thin);
cell.borderBottom(border); // 边框会出现在A2和B2单元格的下方
```
**参考文档:** `cellspan.md`, `cell-style.md`

---
### Q29: 我编写好了一个自定义单元格类型 `MyCustomCellType`，如何将它注册到系统中并在特定单元格上使用它？

**A:** 你需要将你的自定义单元格类型类作为一个属性添加到`GC.Spread.Sheets.CellTypes`命名空间下，然后就可以像使用内置类型一样，通过`new`关键字实例化并应用到单元格上。

```javascript
// 1. 定义你的自定义单元格类型
function MyCustomCellType() {
    GC.Spread.Sheets.CellTypes.Base.call(this);
    this.name("MyCustomCellType");
}
MyCustomCellType.prototype = new GC.Spread.Sheets.CellTypes.Base();
// ... 实现 paint, activateEditor 等方法 ...

// 2. 注册 (通过添加到命名空间)
GC.Spread.Sheets.CellTypes.MyCustomCellType = MyCustomCellType;

// 3. 在单元格上使用
let cell = activeSheet.getCell(0, 0);
cell.cellType(new GC.Spread.Sheets.CellTypes.MyCustomCellType());
```
**参考文档:** `cellcustom.md`, `celltypes.md`

---
### Q30: 我能否创建一个自定义函数，它接收一个数字码，然后返回一个特殊的符号，例如输入65返回大写字母'A'？

**A:** 可以。你可以直接在自定义函数中使用JavaScript的`String.fromCharCode()`方法，这个方法的功能与Excel中的`CHAR`函数完全相同。

```javascript
// 1. 定义并添加自定义函数
function CodeToChar(code) {
    if (typeof code !== 'number') {
        return "#VALUE!";
    }
    return String.fromCharCode(code);
}
spread.addCustomFunction("CODE_TO_CHAR", CodeToChar, {
    name: "CODE_TO_CHAR",
    description: "Returns a character specified by a number.",
    parameters: [{ name: "code" }]
});

// 2. 在单元格中使用
// 在A1输入65
activeSheet.setValue(0, 0, 65);
// 在B1使用公式
activeSheet.getCell(0, 1).formula('=CODE_TO_CHAR(A1)'); // B1将显示 "A"
```
**参考文档:** `calculate-function.md`, `char.md`
