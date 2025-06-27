import { App as AntdApp } from "antd";
import GenericETL from "./GenericETL";

function App() {
    return (
        <AntdApp message={{ maxCount: 3 }}>
            <GenericETL />
        </AntdApp>
    );
}

export default App;
