import "./CustomFooter.css"

const CustomFooter = () => {
    return (
        <footer gc-footer="">
            <div className="gc-footer-container">
                <div className="footer-panel-container">
                    <div className="footer-panel-item">
                        <dl>
                            <dt className="footer-company-info-img">
                                <a href="https://www.grapecity.com.cn" target="_blank" rel="noopener noreferrer">
                                    <img
                                        src="https://cdn.grapecity.com.cn/website-resources/images/metalsmith/logos/gc_cn_s.png"
                                        alt="赋能开发者"
                                    />
                                </a>
                            </dt>
                            <dd>
                                <a href="https://gcdn.grapecity.com.cn" target="_blank" rel="noopener noreferrer">开发者社区</a>
                            </dd>
                            <dd>
                                <a href="https://learn.grapecity.com.cn" target="_blank" rel="noopener noreferrer">开发者学堂</a>
                            </dd>
                            <dd>
                                <a href="https://marketplace.grapecity.com.cn" target="_blank" rel="noopener noreferrer">应用市场</a>
                            </dd>
                            <dd>
                                <a href="https://partner.grapecity.com.cn" target="_blank" rel="noopener noreferrer">生态伙伴中心</a>
                            </dd>
                            <dd>
                                <a href="https://www.grapecity.com.cn/support#goumaizixun" target="_blank" rel="noopener noreferrer">联系葡萄城</a>
                            </dd>
                        </dl>
                    </div>
                    <div className="footer-panel-item">
                        <dl>
                            <dt>
                                Copyright&copy;西安葡萄城软件有限公司 版权所有
                            </dt>
                            <dd>
                                <a href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer">陕ICP备2020018819号</a>
                            </dd>
                        </dl>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default CustomFooter;
