import http from "k6/http";
import { sleep } from "k6";

export const options = {
    discardResponseBodies: true,
    scenarios: {
        contacts: {
            executor: "constant-vus",
            vus: 5,
            duration: "10s",
        },
    },
};

// The function that defines VU logic.
//
// See https://grafana.com/docs/k6/latest/examples/get-started-with-k6/ to learn more
// about authoring k6 scripts.
//

const questions = [
    "活字格支持哪些操作系统和浏览器？",
    "如何在活字格中创建一个新的项目？",
    "我可以在活字格中使用哪些编程语言或脚本？",
    "活字格是否支持数据源的实时更新？",
    "怎样才能提高我在活字格上构建应用的性能？",
    "活字格是否提供API接口来扩展功能？",
    "如何在活字格中实现用户身份验证和授权？",
    "能否将我用活字格制作的应用发布到移动端？",
    "活字格是否支持多语言环境配置？",
    "怎样在活字格中实现数据的导出和导入？",
    "活字格是否有社区或论坛可以寻求帮助？",
    "如何优化活字格中的数据表格加载速度？",
    "活字格支持哪些数据库管理系统？",
    "在活字格中遇到错误时，应该去哪里查找错误日志？",
    "怎样才能让我的活字格应用更符合无障碍设计标准？",
    "活字格是否有教程或案例供初学者学习？",
    "怎样才能使活字格应用适应不同的屏幕尺寸？",
    "活字格是否支持与第三方服务（如支付网关）集成？",
    "如何在活字格中实现表单验证逻辑？",
    "活字格是否提供了版本控制功能来管理代码变更？",
];

export default function () {
    const url = "http://localhost:8000/search/";

    const question =
        questions[Math.floor(Math.random() * questions.length)] +
        " " +
        Math.random();

    const payload = JSON.stringify({
        keyword: question,
        mode: "search",
        product: "forguncy",
    });

    const params = {
        headers: {
            "Content-Type": "application/json",
        },
    };

    _ = http.post(url, payload, params);
    sleep(1);
}
