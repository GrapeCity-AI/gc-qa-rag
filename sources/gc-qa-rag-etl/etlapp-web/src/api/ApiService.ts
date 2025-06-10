const API_BASE = import.meta.env.MODE === "development" ? "http://127.0.0.1:8001/api" : "/api";

export const fetchProducts = async () => {
    const res = await fetch(`${API_BASE}/products`);
    return (await res.json()).products as string[];
};

export const fetchFilesStatus = async (product: string) => {
    const res = await fetch(`${API_BASE}/files_status?product=${product}`);
    return (await res.json()).files as any[];
};

export const createProduct = async (product: string) => {
    const form = new FormData();
    form.append("product", product);
    const res = await fetch(`${API_BASE}/create_product`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) throw new Error((await res.json()).detail || "创建失败");
    return await res.json();
};

export const fetchConfig = async () => {
    const res = await fetch(`${API_BASE}/get_config`);
    return await res.json();
};

export const saveConfig = async (config: any) => {
    const res = await fetch(`${API_BASE}/update_config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error("保存失败");
    return true;
};

export const uploadFile = async (product: string, file: File) => {
    const formData = new FormData();
    formData.append("product", product);
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/das_upload`, {
        method: "POST",
        body: formData,
    });
    if (!res.ok) throw new Error("上传失败");
    return await res.json();
};

export const dasStart = async (product: string, filename: string) => {
    const form = new FormData();
    form.append("product", product);
    form.append("filename", filename);
    const res = await fetch(`${API_BASE}/das_start`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) throw new Error("DAS处理启动失败");
    return await res.json();
};

export const etlStart = async (product: string, etlType: "embedding" | "qa" | "full", filename: string) => {
    const form = new FormData();
    form.append("product", product);
    form.append("etl_type", etlType);
    form.append("filename", filename);
    const res = await fetch(`${API_BASE}/etl_start`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) throw new Error("ETL处理启动失败");
    return await res.json();
};

export const fetchDasResultContent = async (product: string, filename: string) => {
    const res = await fetch(`${API_BASE}/das_result_content?product=${product}&filename=${filename}`);
    if (!res.ok) throw new Error("获取DAS结果失败");
    return await res.json();
};

export const fetchEtlResultContent = async (product: string, etlType: "embedding" | "qa" | "full", filename: string) => {
    const res = await fetch(`${API_BASE}/etl_result_content?product=${product}&etl_type=${etlType}&filename=${filename}`);
    if (!res.ok) throw new Error("获取ETL结果失败");
    return await res.json();
};

export const publish = async (product: string, tag: string) => {
    const form = new FormData();
    form.append("product", product);
    form.append("tag", tag);
    const res = await fetch(`${API_BASE}/publish`, {
        method: "POST",
        body: form,
    });
    if (!res.ok) throw new Error("发布失败");
    return await res.json();
};

export const fetchServerLog = async (lines: number = 100) => {
    const res = await fetch(`${API_BASE}/server_log?lines=${lines}`);
    if (!res.ok) throw new Error("日志获取失败");
    return await res.json();
}; 