/**
 * 简易状态管理器 - 新增ID管理
 */
const StateManager = {
    // 初始状态
    state: {
        isSending: false,       // 是否正在发送消息
        messageList: [],        // 消息列表
        isDarkMode: false,      // 是否深色模式
        lastSendTime: 0,        // 最后发送时间
        userId: "",             // 当前用户ID
        sessionId: ""           // 当前会话ID
    },

    /**
     * 初始化状态
     */
    init() {
        // 从本地存储加载深色模式
        this.state.isDarkMode = localStorage.getItem(AppConfig.STORAGE_KEYS.DARK_MODE) === "true";

        // 初始化ID（优先从本地存储读取，无则生成）
        const { userId, sessionId } = IdUtils.getIdsFromStorage();
        this.state.userId = userId;
        this.state.sessionId = sessionId;
    },

    /**
     * 更新状态
     * @param {Object} newState 要更新的状态
     */
    update(newState) {
        this.state = { ...this.state, ...newState };
        // 持久化状态
        if (newState.isDarkMode !== undefined) {
            localStorage.setItem(AppConfig.STORAGE_KEYS.DARK_MODE, newState.isDarkMode);
        }
        // 持久化ID
        if (newState.userId || newState.sessionId) {
            IdUtils.saveIdsToStorage(
                newState.userId || this.state.userId,
                newState.sessionId || this.state.sessionId
            );
        }
    },

    /**
     * 获取当前状态
     * @returns {Object} 当前状态
     */
    getState() {
        return { ...this.state }; // 返回副本，防止直接修改
    },

    /**
     * 添加消息到列表
     * @param {Object} message 消息对象 {sender, content, time, isMiddle = false}
     */
    addMessage(message) {
        const newList = [...this.state.messageList, message];
        this.update({ messageList: newList });
    },

    /**
     * 更新中间过程消息
     * @param {string} placeholderId 占位消息ID
     * @param {string} content 新的中间内容
     */
    updateMiddleMessage(placeholderId, content) {
        const newList = this.state.messageList.map(msg => {
            if (msg.id === placeholderId) {
                return { ...msg, content, isMiddle: true };
            }
            return msg;
        });
        this.update({ messageList: newList });
    },

    /**
     * 替换中间消息为最终结果
     * @param {string} placeholderId 占位消息ID
     * @param {string} finalContent 最终内容
     */
    replaceMiddleToFinal(placeholderId, finalContent) {
        const newList = this.state.messageList.map(msg => {
            if (msg.id === placeholderId) {
                return { ...msg, content: finalContent, isMiddle: false };
            }
            return msg;
        });
        this.update({ messageList: newList });
    },

    /**
     * 更新 ID
     * @param {string} userId
     * @param {string} sessionId
     */
    updateIds(userId, sessionId) {
        this.update({ userId, sessionId });
    },

    /**
     * 删除消息
     * @param {string} messageId 消息 ID
     */
    deleteMessage(messageId) {
        const newList = this.state.messageList.filter(msg => msg.id !== messageId);
        this.update({ messageList: newList });
    },

    /**
     * 更新消息内容
     * @param {string} messageId 消息 ID
     * @param {string} content 新内容
     * @param {boolean} isMiddle 是否为中间消息
     */
    updateMessageContent(messageId, content, isMiddle = false) {
        const newList = this.state.messageList.map(msg => {
            if (msg.id === messageId) {
                return { ...msg, content, isMiddle };
            }
            return msg;
        });
        this.update({ messageList: newList });
    }
};