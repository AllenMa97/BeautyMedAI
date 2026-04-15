/**
 * 全局配置文件
 * 集中管理所有可配置项，便于维护
 */
const AppConfig = {
    // 后端接口地址
    API_BASE_URL: "http://10.3.3.205:6732",
    // 聊天接口路径
    CHAT_API_PATH: "/api/v1/entrance",
    // 防抖时间（ms）
    DEBOUNCE_TIME: 500,
    // 快捷表情列表
    EMOTICONS: ["😊", "😂", "🤔", "👍", "👋", "😎", "🤩", "💡"],
    // 本地存储key
    STORAGE_KEYS: {
        DARK_MODE: "darkMode",
        MESSAGE_HISTORY: "messageHistory", // 可选：存储聊天记录
        API_CONFIG: "apiConfig" // 存储API配置
    }
};

// 从本地存储加载API配置
const savedApiConfig = localStorage.getItem(AppConfig.STORAGE_KEYS.API_CONFIG);
if (savedApiConfig) {
    try {
        const config = JSON.parse(savedApiConfig);
        if (config.apiBaseUrl) {
            AppConfig.API_BASE_URL = config.apiBaseUrl;
        }
    } catch (e) {
        console.error('加载API配置失败:', e);
    }
}