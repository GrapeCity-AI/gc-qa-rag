import * as React from "react";
import "./App.css";
import { ConfigProvider, Flex } from "antd";

import { HashRouter as Router, Route, Routes } from "react-router-dom";

const HomePage = React.lazy(() => import("./views/Home"));
const ChatPage = React.lazy(() => import("./views/Chat"));
const SearchPage = React.lazy(() => import("./views/Search"));

function App() {
    return (
        <ConfigProvider theme={{ token: { borderRadius: 4 } }}>
            <Router>
                <Routes>
                    <Route
                        path="/"
                        element={
                            <Flex gap="middle" vertical align="center">
                                <React.Suspense fallback={<div />}>
                                    <HomePage />
                                </React.Suspense>
                            </Flex>
                        }
                    ></Route>
                    <Route
                        path="/home"
                        element={
                            <Flex gap="middle" vertical align="center">
                                <React.Suspense fallback={<div />}>
                                    <HomePage />
                                </React.Suspense>
                            </Flex>
                        }
                    ></Route>
                    <Route
                        path="/chat"
                        element={
                            <Flex gap="middle" vertical align="center">
                                <React.Suspense fallback={<div />}>
                                    <ChatPage />
                                </React.Suspense>
                            </Flex>
                        }
                    ></Route>
                    <Route
                        path="/search"
                        element={
                            <Flex gap="middle" vertical align="center">
                                <React.Suspense fallback={<div />}>
                                    <SearchPage />
                                </React.Suspense>
                            </Flex>
                        }
                    ></Route>
                </Routes>
            </Router>
        </ConfigProvider>
    );
}

export default App;
