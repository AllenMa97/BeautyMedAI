/**
 * 流式聊天接口封装 - 适配ID传递
 */
const ChatApi = {
    /**
     * 上传文件到服务器
     * @param {File} file 要上传的文件
     * @param {string} userId 用户ID
     * @param {string} sessionId 会话ID
     * @returns {Promise<string>} 上传后的文件URL
     */
    async uploadFile(file, userId = "", sessionId = "") {
        const url = `${AppConfig.API_BASE_URL}${AppConfig.UPLOAD_API_PATH || '/upload'}`;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId);
        formData.append('session_id', sessionId);

        try {
            const response = await fetch(url, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                throw new Error('文件上传失败');
            }

            const data = await response.json();
            return data.url || `https://example.com/images/${file.name}`;
        } catch (error) {
            console.error("文件上传失败：", error);
            throw error;
        }
    },

    /**
     * 流式发送消息到规划器接口
     * @param {string} userInput 用户输入
     * @param {string} sessionId 会话ID
     * @param {string} userId 用户ID
     * @param {string} context 对话上下文JSON字符串
     * @param {Function} onChunk 流式回调：每收到一个chunk就调用 (chunkData) => {}
     * @param {Function} onComplete 完成回调：最终结果（code:200）时调用 (finalData) => {}
     * @param {Function} onTyping 完成回调：流式打字（code:300）时调用 (typingData) => {}
     * @param {Function} onForbidden 违规回调：code:403时调用 (data) => {}
     * @param {Function} onError 错误回调
     */
    async sendStreamMessage(
        userInput,
        sessionId = "",
        userId = "",
        context = "[]",
        lang = "zh-CN",
        onChunk = () => {},
        onComplete = () => {},
        onTyping = () => {},
        onForbidden = () => {},
        onError = () => {}
    ) {
        const url = `${AppConfig.API_BASE_URL}${AppConfig.CHAT_API_PATH}`;
        const requestBody = {
            session_id: sessionId,       // 使用当前会话ID
            user_id: userId,             // 使用当前用户ID
            lang: lang,
            data: null,
            stream_flag: true,           // 开启流式返回
            user_input: userInput,
            context: context
        };

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json();
                onError(errorData);
                return;
            }

            // 流式读取响应体
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                // 把二进制转成字符串，拼到缓冲区
                buffer += decoder.decode(value, { stream: true });

                // 按换行符分割，逐行处理 SSE 格式
                const lines = buffer.split("\n");
                buffer = lines.pop(); // 最后一行可能不完整，留到下次

                for (const line of lines) {
                    if (!line.trim()) continue; // 跳过空行
                    if (line.startsWith("data: ")) {
                        const jsonStr = line.slice(6).trim(); // 去掉 "data: " 前缀
                        try {
                            const chunk = JSON.parse(jsonStr);
                            console.log('[SSE] 收到数据包, code:', chunk.code);
                            
                            // 根据状态码处理不同的回调
                            if (chunk.code === 200) {
                                console.log('[SSE] 调用 onComplete (200)');
                                onComplete(chunk);
                                return;
                            } else if (chunk.code === 300) {
                                console.log('[SSE] 调用 onTyping (300)');
                                onTyping(chunk);
                            } else if (chunk.code === 403) {
                                console.log('[SSE] 调用 onForbidden (403)');
                                onForbidden(chunk);
                            } else {
                                console.log('[SSE] 调用 onChunk (102)');
                                onChunk(chunk);
                            }
                        } catch (e) {
                            console.warn("解析流式chunk失败：", e, "原始行：", line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error("流式请求失败：", error);
            onError(error);
        }
    }
};