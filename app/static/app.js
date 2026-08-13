const questionInput = document.getElementById("questionInput")
const sendButton = document.getElementById("sendButton")
const sendButtonLabel = document.getElementById("sendButtonLabel")
const answerBox = document.getElementById("answerBox")
const sourcesBox = document.getElementById("sourcesBox")
const sourcePanel = document.getElementById("sourcePanel")
const chatScroll = document.getElementById("chatScroll")
const modelBadge = document.getElementById("modelBadge")
const currentModelName = document.getElementById("currentModelName")

const authScreen = document.getElementById("authScreen")
const authForm = document.getElementById("authForm")
const loginTabButton = document.getElementById("loginTabButton")
const registerTabButton = document.getElementById("registerTabButton")
const authTitle = document.getElementById("authTitle")
const authDescription = document.getElementById("authDescription")
const authUsernameInput = document.getElementById("authUsernameInput")
const authPasswordInput = document.getElementById("authPasswordInput")
const authConfirmPasswordInput = document.getElementById("authConfirmPasswordInput")
const confirmPasswordField = document.getElementById("confirmPasswordField")
const authStatus = document.getElementById("authStatus")
const authSubmitButton = document.getElementById("authSubmitButton")
const authSubmitLabel = document.getElementById("authSubmitLabel")
const currentUsername = document.getElementById("currentUsername")
const currentUserInitial = document.getElementById("currentUserInitial")
const currentUserRole = document.getElementById("currentUserRole")
const logoutButton = document.getElementById("logoutButton")
const loadHistoryButton = document.getElementById("loadHistoryButton")
const historyStatus = document.getElementById("historyStatus")
const historyList = document.getElementById("historyList")
const conversationSidebar = document.getElementById("conversationSidebar")
const conversationList = document.getElementById("conversationList")
const conversationStatus = document.getElementById("conversationStatus")
const newConversationButton = document.getElementById("newConversationButton")
const loadMoreConversationsButton = document.getElementById("loadMoreConversationsButton")
const loadOlderMessagesButton = document.getElementById("loadOlderMessagesButton")
const mobileConversationButton = document.getElementById("mobileConversationButton")
const closeConversationButton = document.getElementById("closeConversationButton")
const conversationBackdrop = document.getElementById("conversationBackdrop")

const fileInput = document.getElementById("fileInput")
const dropZone = document.getElementById("dropZone")
const selectedFileName = document.getElementById("selectedFileName")
const overwriteInput = document.getElementById("overwriteInput")
const uploadButton = document.getElementById("uploadButton")
const uploadStatus = document.getElementById("uploadStatus")
const rebuildButton = document.getElementById("rebuildButton")
const buildProgress = document.getElementById("buildProgress")
const buildProgressIndicator = document.getElementById("buildProgressIndicator")
const buildProgressTitle = document.getElementById("buildProgressTitle")
const buildProgressMessage = document.getElementById("buildProgressMessage")
const buildProgressSteps = document.getElementById("buildProgressSteps")

const documentCount = document.getElementById("documentCount")
const documentList = document.getElementById("documentList")
const documentStatus = document.getElementById("documentStatus")
const documentSearchInput = document.getElementById("documentSearchInput")
const documentFormatButtons = document.querySelectorAll("[data-format]")
const documentDetail = document.getElementById("documentDetail")
const detailFilename = document.getElementById("detailFilename")
const detailMetadata = document.getElementById("detailMetadata")
const detailContent = document.getElementById("detailContent")
const detailChunks = document.getElementById("detailChunks")
const detailChunkCount = document.getElementById("detailChunkCount")
const originalTextTab = document.getElementById("originalTextTab")
const documentChunksTab = document.getElementById("documentChunksTab")
const closeDetailButton = document.getElementById("closeDetailButton")

const knowledgeSection = document.getElementById("knowledgeSection")
const appShell = document.getElementById("appShell")
const mobileKnowledgeButton = document.getElementById("mobileKnowledgeButton")
const closeKnowledgeButton = document.getElementById("closeKnowledgeButton")
const sidebarBackdrop = document.getElementById("sidebarBackdrop")

const statsStatus = document.getElementById("statsStatus")
const statsDocumentCount = document.getElementById("statsDocumentCount")
const statsChunkCount = document.getElementById("statsChunkCount")
const statsVectorCount = document.getElementById("statsVectorCount")
const statsThreshold = document.getElementById("statsThreshold")
const statsTopK = document.getElementById("statsTopK")
const statsScoreGap = document.getElementById("statsScoreGap")
const statsFormats = document.getElementById("statsFormats")
const statsBuiltAt = document.getElementById("statsBuiltAt")

let openedDocumentName = null
let selectedUploadFile = null
let allDocuments = []
let selectedDocumentFormat = "all"
let knowledgeOperationRunning = false
let currentConversationId = null
let conversations = []
let conversationPage = 1
let conversationHasMore = false
let messagePage = 1
let messageHasMore = false
let authMode = "login"
let currentUser = null
const ACCESS_TOKEN_KEY = "zhixiaoku_access_token"
let conversationCollapsed = (
    localStorage.getItem("conversationSidebarCollapsed") === "true"
)
let knowledgeCollapsed = (
    localStorage.getItem("knowledgeSidebarCollapsed") === "true"
)

function setKnowledgeOperationRunning(running) {
    knowledgeOperationRunning = running
    uploadButton.disabled = running
    rebuildButton.disabled = running
    fileInput.disabled = running
    overwriteInput.disabled = running

    for (const deleteButton of documentList.querySelectorAll(
        ".dangerButton"
    )) {
        deleteButton.disabled = running
    }
}

const buildStages = [
    {key: "reading", label: "读取与解析文档"},
    {key: "splitting", label: "切分文本片段"},
    {key: "embedding", label: "生成Embedding向量"},
    {key: "saving", label: "保存FAISS索引"},
    {key: "reloading", label: "重新加载运行时"}
]

function getErrorInfo(data, fallbackMessage) {
    const detail = data?.detail

    if (typeof detail === "string") {
        return {stage: null, message: detail}
    }

    if (detail && typeof detail === "object") {
        return {
            stage: detail.stage || null,
            message: detail.message || fallbackMessage
        }
    }

    return {stage: null, message: fallbackMessage}
}

function getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
}

function setAccessToken(token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

function clearAccessToken() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
}

function authHeaders(headers = {}) {
    const token = getAccessToken()

    return {
        ...headers,
        ...(token
            ? {Authorization: `Bearer ${token}`}
            : {})
    }
}

async function authenticatedFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: authHeaders(options.headers || {})
    })

    if (response.status === 401) {
        showAuthScreen("登录状态已过期，请重新登录")
    }

    return response
}

function showAuthScreen(message = "") {
    clearAccessToken()
    currentUser = null
    currentConversationId = null
    conversations = []
    conversationPage = 1
    messagePage = 1
    appShell.hidden = true
    authScreen.hidden = false
    authStatus.textContent = message
    authStatus.classList.toggle("isError", Boolean(message))
    authPasswordInput.value = ""
    authConfirmPasswordInput.value = ""
    authUsernameInput.focus()
}

function showApplication(user) {
    currentUser = user
    currentUsername.textContent = user.username
    currentUserRole.textContent = user.role === "admin"
        ? "管理员"
        : "普通用户"
    currentUserInitial.textContent = (
        user.username.trim().charAt(0).toUpperCase() || "U"
    )
    authScreen.hidden = true
    appShell.hidden = false

    for (const element of document.querySelectorAll(".adminOnly")) {
        element.hidden = user.role !== "admin"
    }
}

function setAuthMode(mode) {
    authMode = mode
    const isRegister = mode === "register"

    loginTabButton.classList.toggle("isActive", !isRegister)
    registerTabButton.classList.toggle("isActive", isRegister)
    loginTabButton.setAttribute("aria-selected", String(!isRegister))
    registerTabButton.setAttribute("aria-selected", String(isRegister))
    confirmPasswordField.hidden = !isRegister
    authConfirmPasswordInput.required = isRegister
    authPasswordInput.autocomplete = isRegister
        ? "new-password"
        : "current-password"
    authTitle.textContent = isRegister ? "创建知晓库账号" : "登录知晓库"
    authDescription.textContent = isRegister
        ? "注册后即可拥有独立的知识库会话空间"
        : "登录后继续使用你的知识库与会话记录"
    authSubmitLabel.textContent = isRegister ? "注册并登录" : "登录"
    authStatus.textContent = ""
    authStatus.classList.remove("isError", "isSuccess")
}

async function requestLogin(username, password) {
    const response = await fetch("/auth/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username, password})
    })
    const data = await response.json()

    if (!response.ok) {
        throw new Error(data.detail || "登录失败")
    }

    setAccessToken(data.access_token)
    return data
}

async function loadCurrentUser() {
    const response = await authenticatedFetch("/auth/me")

    if (!response.ok) {
        return null
    }

    return response.json()
}

async function submitAuthForm(event) {
    event.preventDefault()

    const username = authUsernameInput.value.trim()
    const password = authPasswordInput.value

    if (authMode === "register") {
        if (password !== authConfirmPasswordInput.value) {
            authStatus.textContent = "两次输入的密码不一致"
            authStatus.classList.add("isError")
            return
        }
    }

    authSubmitButton.disabled = true
    authSubmitLabel.textContent = authMode === "register"
        ? "正在注册…"
        : "正在登录…"
    authStatus.textContent = ""
    authStatus.classList.remove("isError", "isSuccess")

    try {
        if (authMode === "register") {
            const registerResponse = await fetch("/auth/register", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username, password})
            })
            const registerData = await registerResponse.json()

            if (!registerResponse.ok) {
                throw new Error(registerData.detail || "注册失败")
            }
        }

        await requestLogin(username, password)
        const user = await loadCurrentUser()

        if (!user) {
            throw new Error("用户信息读取失败")
        }

        showApplication(user)
        await initializeApplication()
    } catch (error) {
        clearAccessToken()
        authStatus.textContent = error.message || "认证失败"
        authStatus.classList.add("isError")
    } finally {
        authSubmitButton.disabled = false
        authSubmitLabel.textContent = authMode === "register"
            ? "注册并登录"
            : "登录"
    }
}

async function restoreSession() {
    if (!getAccessToken()) {
        showAuthScreen()
        return
    }

    const user = await loadCurrentUser()

    if (!user) {
        return
    }

    showApplication(user)
    await initializeApplication()
}

function renderBuildProgress(status, options = {}) {
    const failedStageIndex = buildStages.findIndex(
        stage => stage.key === options.failedStage
    )

    buildProgress.hidden = false
    buildProgress.className = `buildProgress is-${status}`
    buildProgressTitle.textContent = options.title || "正在建立知识库"
    buildProgressMessage.textContent = options.message || "后端正在依次执行以下步骤"
    buildProgressIndicator.textContent = status === "success" ? "✓" : status === "error" ? "!" : ""
    buildProgressSteps.replaceChildren()

    for (const [index, stage] of buildStages.entries()) {
        const step = document.createElement("li")
        const stepMarker = document.createElement("span")
        const stepLabel = document.createElement("span")

        step.dataset.stage = stage.key
        stepMarker.className = "buildStepMarker"
        stepLabel.textContent = stage.label

        if (status === "success") {
            step.className = "isComplete"
            stepMarker.textContent = "✓"
        } else if (status === "error") {
            if (index < failedStageIndex) {
                step.className = "isComplete"
                stepMarker.textContent = "✓"
            } else if (index === failedStageIndex) {
                step.className = "isFailed"
                stepMarker.textContent = "!"
            } else {
                step.className = "isPending"
                stepMarker.textContent = "·"
            }
        } else {
            step.className = "isProcessing"
            stepMarker.textContent = "·"
        }

        step.append(stepMarker, stepLabel)
        buildProgressSteps.appendChild(step)
    }
}

function appendInlineMarkdown(container, text) {
    const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g
    let lastIndex = 0

    for (const match of text.matchAll(pattern)) {
        if (match.index > lastIndex) {
            container.append(
                document.createTextNode(
                    text.slice(lastIndex, match.index)
                )
            )
        }

        const token = match[0]
        let element

        if (token.startsWith("**")) {
            element = document.createElement("strong")
            element.textContent = token.slice(2, -2)
        } else if (token.startsWith("`")) {
            element = document.createElement("code")
            element.textContent = token.slice(1, -1)
        } else {
            element = document.createElement("em")
            element.textContent = token.slice(1, -1)
        }

        container.appendChild(element)
        lastIndex = match.index + token.length
    }

    if (lastIndex < text.length) {
        container.append(
            document.createTextNode(
                text.slice(lastIndex)
            )
        )
    }
}

function renderMarkdownText(container, text) {
    const lines = text.split("\n")
    let activeList = null
    let activeListType = null

    for (const rawLine of lines) {
        const line = rawLine.trim()

        if (!line) {
            activeList = null
            activeListType = null
            continue
        }

        const headingMatch = line.match(/^(#{1,3})\s+(.+)$/)
        const unorderedMatch = line.match(/^[-*]\s+(.+)$/)
        const orderedMatch = line.match(/^\d+\.\s+(.+)$/)
        const quoteMatch = line.match(/^>\s?(.+)$/)

        if (headingMatch) {
            activeList = null
            activeListType = null

            const heading = document.createElement(
                `h${headingMatch[1].length}`
            )

            appendInlineMarkdown(heading, headingMatch[2])
            container.appendChild(heading)
            continue
        }

        if (unorderedMatch || orderedMatch) {
            const listType = unorderedMatch ? "ul" : "ol"
            const listText = unorderedMatch
                ? unorderedMatch[1]
                : orderedMatch[1]

            if (!activeList || activeListType !== listType) {
                activeList = document.createElement(listType)
                activeListType = listType
                container.appendChild(activeList)
            }

            const item = document.createElement("li")
            appendInlineMarkdown(item, listText)
            activeList.appendChild(item)
            continue
        }

        activeList = null
        activeListType = null

        const block = document.createElement(
            quoteMatch ? "blockquote" : "p"
        )

        appendInlineMarkdown(
            block,
            quoteMatch ? quoteMatch[1] : line
        )

        container.appendChild(block)
    }
}

function renderMarkdown(content) {
    const wrapper = document.createElement("div")
    wrapper.className = "markdownContent"

    const parts = String(content).split(/```([\s\S]*?)```/g)

    for (let index = 0; index < parts.length; index += 1) {
        const part = parts[index]

        if (!part) {
            continue
        }

        if (index % 2 === 1) {
            const pre = document.createElement("pre")
            const code = document.createElement("code")

            code.textContent = part.trim()
            pre.appendChild(code)
            wrapper.appendChild(pre)
        } else {
            renderMarkdownText(wrapper, part)
        }
    }

    return wrapper
}

function createMessageRow(role, content, thinking = false) {
    const isUser = role === "user"
    const row = document.createElement("div")
    const avatar = document.createElement("div")
    const bubble = document.createElement("article")
    const roleLabel = document.createElement("span")

    row.className = isUser
        ? "messageRow userMessage"
        : "messageRow assistantMessage"

    avatar.className = "messageAvatar"
    avatar.textContent = isUser ? "你" : "AI"

    bubble.className = "historyMessage"
    roleLabel.className = "messageRole"
    roleLabel.textContent = isUser ? "You" : "小库"

    bubble.appendChild(roleLabel)

    if (thinking) {
        const dots = document.createElement("div")
        dots.className = "thinkingDots"

        for (let index = 0; index < 3; index += 1) {
            dots.appendChild(document.createElement("span"))
        }

        bubble.appendChild(dots)
    } else {
        bubble.appendChild(renderMarkdown(content))
    }

    if (isUser) {
        row.append(bubble, avatar)
    } else {
        row.append(avatar, bubble)
    }

    return row
}

function scrollChatToBottom() {
    requestAnimationFrame(function () {
        chatScroll.scrollTop = chatScroll.scrollHeight
    })
}

function showHistory(messages) {
    historyList.replaceChildren()

    if (messages.length === 0) {
        const emptyState = document.createElement("div")
        emptyState.className = "emptyConversation"
        emptyState.textContent = "还没有对话，试着问一个知识库相关的问题。"
        historyList.appendChild(emptyState)
        return
    }

    for (const message of messages) {
        historyList.appendChild(
            createMessageRow(
                message.role,
                message.content
            )
        )
    }

    scrollChatToBottom()
}

function showThinkingState(question) {
    const emptyState = historyList.querySelector(".emptyConversation")

    if (emptyState) {
        emptyState.remove()
    }

    historyList.appendChild(
        createMessageRow("user", question)
    )

    historyList.appendChild(
        createMessageRow("assistant", "", true)
    )

    scrollChatToBottom()
}

function showSources(sources) {
    sourcesBox.replaceChildren()
    sourcePanel.hidden = false

    if (sources.length === 0) {
        sourcesBox.textContent = "本次回答没有检索到相关来源。"
        return
    }

    for (const [index, source] of sources.entries()) {
        const sourceItem = document.createElement("article")
        const sourceMeta = document.createElement("p")
        const sourceName = document.createElement("span")
        const sourceBadges = document.createElement("span")
        const sourceLength = document.createElement("span")
        const score = document.createElement("span")
        const sourceContent = document.createElement("pre")

        sourceItem.className = "sourceItem"
        sourceMeta.className = "sourceMeta"
        sourceBadges.className = "sourceBadges"
        sourceLength.className = "sourceLength"
        score.className = "scoreBadge"

        const pageLabel = source.page_number
            ? ` · 第 ${source.page_number} 页`
            : ""

        sourceName.textContent =
            `Top ${index + 1} · ${source.source}` +
            `${pageLabel} · 片段 ${source.chunk_id}`

        sourceLength.textContent = `${source.content.length} 字符`
        score.textContent = `相似度 ${source.score}`
        sourceContent.textContent = source.content

        sourceBadges.append(sourceLength, score)
        sourceMeta.append(sourceName, sourceBadges)
        sourceItem.append(sourceMeta, sourceContent)
        sourcesBox.appendChild(sourceItem)
    }

    scrollChatToBottom()
}

function showDocumentDetailView(viewName) {
    const showOriginal = viewName === "original"

    detailContent.hidden = !showOriginal
    detailChunks.hidden = showOriginal
    originalTextTab.classList.toggle("isActive", showOriginal)
    documentChunksTab.classList.toggle("isActive", !showOriginal)
    originalTextTab.setAttribute("aria-selected", String(showOriginal))
    documentChunksTab.setAttribute("aria-selected", String(!showOriginal))
}

function renderDocumentChunks(chunks) {
    detailChunks.replaceChildren()
    detailChunkCount.textContent = chunks.length

    if (chunks.length === 0) {
        const emptyMessage = document.createElement("p")
        emptyMessage.className = "chunkEmptyState"
        emptyMessage.textContent = "该文档暂时没有分块数据，请尝试重新建库。"
        detailChunks.appendChild(emptyMessage)
        return
    }

    for (const chunk of chunks) {
        const chunkItem = document.createElement("article")
        const chunkHeader = document.createElement("div")
        const chunkTitle = document.createElement("strong")
        const chunkLength = document.createElement("span")
        const chunkContent = document.createElement("pre")

        chunkItem.className = "chunkItem"
        chunkHeader.className = "chunkHeader"
        const pageLabel = chunk.page_number
            ? ` · 第 ${chunk.page_number} 页`
            : ""

        chunkTitle.textContent =
            `片段 ${chunk.chunk_id}${pageLabel}`
        chunkLength.textContent = `${chunk.character_count} 字符`
        chunkContent.textContent = chunk.content

        chunkHeader.append(chunkTitle, chunkLength)
        chunkItem.append(chunkHeader, chunkContent)
        detailChunks.appendChild(chunkItem)
    }
}

function formatModelName(modelName) {
    if (!modelName) {
        return "未配置"
    }

    const shortName = modelName
        .split("/")
        .pop()

    return shortName.replace(/[-_]+/g, " ")
}

async function loadModelInfo() {
    try {
        const response = await fetch("/system/info")
        const data = await response.json()

        if (!response.ok) {
            currentModelName.textContent = "读取失败"
            return
        }

        currentModelName.textContent =
            formatModelName(data.llm_model)

        modelBadge.title =
            `当前使用模型：${data.llm_model || "未配置"}`

    } catch (error) {
        console.error(error)
        currentModelName.textContent = "读取失败"
    }
}

async function loadLegacyHistory() {
    loadHistoryButton.disabled = true
    historyStatus.textContent = "正在加载聊天记录……"

    try {
        const response = await authenticatedFetch(
            "/rag/history?limit=20"
        )

        const data = await response.json()

        if (!response.ok) {
            historyStatus.textContent =
                data.detail || "聊天记录加载失败"

            return
        }

        showHistory(data.messages)

        historyStatus.textContent =
            `最近 ${data.messages.length} 条消息`

    } catch (error) {
        console.error(error)
        historyStatus.textContent = "无法连接到服务器"

    } finally {
        loadHistoryButton.disabled = false
    }
}

function renderConversations() {
    conversationList.replaceChildren()

    if (conversations.length === 0) {
        const emptyItem = document.createElement("li")
        emptyItem.className = "conversationEmptyState"
        emptyItem.textContent = "暂无会话，点击上方按钮开始提问"
        conversationList.appendChild(emptyItem)
        return
    }

    for (const conversation of conversations) {
        const item = document.createElement("li")
        const button = document.createElement("button")
        const deleteButton = document.createElement("button")
        const title = document.createElement("strong")
        const time = document.createElement("span")

        item.className = "conversationItem"

        button.type = "button"
        button.className = "conversationItemButton"
        button.classList.toggle(
            "isActive",
            conversation.id === currentConversationId
        )

        title.textContent = conversation.title || "新对话"
        time.textContent = formatDate(
            conversation.updated_at
        )

        button.append(title, time)
        button.addEventListener("click", function () {
            selectConversation(conversation.id)
        })

        deleteButton.type = "button"
        deleteButton.className = "conversationDeleteButton"
        deleteButton.textContent = "×"
        deleteButton.title = `删除会话：${title.textContent}`
        deleteButton.setAttribute(
            "aria-label",
            `删除会话：${title.textContent}`
        )
        deleteButton.addEventListener("click", function () {
            deleteConversation(conversation, deleteButton)
        })

        item.append(button, deleteButton)
        conversationList.appendChild(item)
    }
}

async function loadConversationMessages() {
    if (currentConversationId === null) {
        showHistory([])
        historyStatus.textContent = "新建或选择一个会话后开始提问"
        loadOlderMessagesButton.hidden = true
        return
    }

    historyStatus.textContent = "正在加载当前会话…"

    try {
        const response = await authenticatedFetch(
            `/rag/conversations/${currentConversationId}/messages`
            + `?page=${messagePage}&page_size=20`
        )
        const data = await response.json()

        if (!response.ok) {
            historyStatus.textContent =
                data.detail || "会话消息加载失败"
            return
        }

        const previousScrollHeight = chatScroll.scrollHeight

        if (messagePage === 1) {
            showHistory(data.messages)
        } else {
            const fragment = document.createDocumentFragment()

            for (const message of data.messages) {
                fragment.appendChild(
                    createMessageRow(message.role, message.content)
                )
            }

            historyList.prepend(fragment)

            requestAnimationFrame(function () {
                chatScroll.scrollTop =
                    chatScroll.scrollHeight - previousScrollHeight
            })
        }

        messageHasMore = data.has_more
        loadOlderMessagesButton.hidden = !messageHasMore
        historyStatus.textContent =
            `${data.conversation.title} · 已加载 ${historyList.children.length} 条消息`

    } catch (error) {
        console.error(error)
        historyStatus.textContent = "无法连接到服务器"
    }
}

async function selectConversation(conversationId) {
    currentConversationId = conversationId
    messagePage = 1
    sourcePanel.hidden = true
    renderConversations()
    await loadConversationMessages()

    if (isConversationDrawerMode()) {
        closeConversationSidebar()
    }
}

async function loadConversations(
    loadSelected = true,
    append = false
) {
    if (!append) {
        conversationPage = 1
    }

    loadHistoryButton.disabled = true
    conversationStatus.textContent = "正在加载会话…"

    try {
        const response = await authenticatedFetch(
            `/rag/conversations?page=${conversationPage}&page_size=20`
        )
        const data = await response.json()

        if (!response.ok) {
            conversationStatus.textContent =
                data.detail || "会话列表加载失败"
            return
        }

        const loadedConversations = data.conversations || []
        conversations = append
            ? [...conversations, ...loadedConversations]
            : loadedConversations
        conversationHasMore = data.has_more
        loadMoreConversationsButton.hidden = !conversationHasMore

        const currentStillExists = conversations.some(
            conversation => (
                conversation.id === currentConversationId
            )
        )

        if (!currentStillExists) {
            currentConversationId =
                conversations[0]?.id ?? null
            messagePage = 1
        }

        renderConversations()
        conversationStatus.textContent =
            `${conversations.length} 个会话`

        if (loadSelected && !append) {
            await loadConversationMessages()
        }

    } catch (error) {
        console.error(error)
        conversationStatus.textContent = "无法连接到服务器"

    } finally {
        loadHistoryButton.disabled = false
    }
}

async function createConversation() {
    newConversationButton.disabled = true
    conversationStatus.textContent = "正在创建新会话…"

    try {
        const response = await authenticatedFetch(
            "/rag/conversations",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    title: "新对话"
                })
            }
        )
        const data = await response.json()

        if (!response.ok) {
            conversationStatus.textContent =
                data.detail || "新建会话失败"
            return null
        }

        currentConversationId = data.id
        conversationPage = 1
        messagePage = 1
        sourcePanel.hidden = true
        await loadConversations(true)
        questionInput.focus()
        return data.id

    } catch (error) {
        console.error(error)
        conversationStatus.textContent = "无法连接到服务器"
        return null

    } finally {
        newConversationButton.disabled = false
    }
}

async function deleteConversation(
    conversation,
    deleteButton
) {
    const confirmed = window.confirm(
        `确定删除会话“${conversation.title || "新对话"}”吗？\n`
        + "该会话中的聊天记录也会一并删除。"
    )

    if (!confirmed) {
        return
    }

    deleteButton.disabled = true
    conversationStatus.textContent = "正在删除会话…"

    try {
        const response = await authenticatedFetch(
            `/rag/conversations/${conversation.id}`,
            {method: "DELETE"}
        )
        const data = await response.json()

        if (!response.ok) {
            conversationStatus.textContent =
                data.detail || "会话删除失败"
            deleteButton.disabled = false
            return
        }

        const deletedCurrentConversation = (
            conversation.id === currentConversationId
        )

        if (deletedCurrentConversation) {
            currentConversationId = null
            messagePage = 1
            sourcePanel.hidden = true
        }

        await loadConversations(
            deletedCurrentConversation
        )

    } catch (error) {
        console.error(error)
        conversationStatus.textContent = "无法连接到服务器"
        deleteButton.disabled = false
    }
}

async function loadHistory() {
    await loadConversations(true)
}

async function loadMoreConversations() {
    if (!conversationHasMore) {
        return
    }

    conversationPage += 1
    loadMoreConversationsButton.disabled = true

    try {
        await loadConversations(false, true)
    } finally {
        loadMoreConversationsButton.disabled = false
    }
}

async function loadOlderMessages() {
    if (!messageHasMore || currentConversationId === null) {
        return
    }

    messagePage += 1
    loadOlderMessagesButton.disabled = true

    try {
        await loadConversationMessages()
    } finally {
        loadOlderMessagesButton.disabled = false
    }
}

function formatFileSize(sizeBytes) {
    if (sizeBytes < 1024) {
        return `${sizeBytes} B`
    }

    return `${(sizeBytes / 1024).toFixed(1)} KB`
}

function formatDate(value) {
    const date = new Date(value)

    if (Number.isNaN(date.getTime())) {
        return value
    }

    return date.toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    })
}

async function loadKnowledgeStats() {
    statsStatus.textContent = "正在加载"

    try {
        const response = await authenticatedFetch("/knowledge/stats")
        const data = await response.json()

        if (!response.ok) {
            statsStatus.textContent = "加载失败"
            return
        }

        statsDocumentCount.textContent = data.document_count
        statsChunkCount.textContent = data.chunk_count
        statsVectorCount.textContent = data.vector_count
        statsThreshold.textContent = data.threshold
        statsTopK.textContent = data.top_k
        statsScoreGap.textContent = data.score_gap
        statsFormats.textContent = data.supported_formats.join(" · ")
        statsBuiltAt.textContent = data.last_built_at
            ? `最近建库：${formatDate(data.last_built_at)}`
            : "最近建库：暂无记录"
        statsStatus.textContent = "运行正常"

    } catch (error) {
        console.error(error)
        statsStatus.textContent = "连接失败"
    }
}

function getDocumentExtension(filename) {
    const extensionPosition = filename.lastIndexOf(".")

    if (extensionPosition === -1) {
        return ""
    }

    return filename.slice(extensionPosition + 1).toLowerCase()
}

function renderDocuments() {
    documentList.replaceChildren()

    const keyword = documentSearchInput.value.trim().toLowerCase()
    const filteredDocuments = allDocuments.filter(documentItem => {
        const matchesKeyword = documentItem.filename
            .toLowerCase()
            .includes(keyword)
        const matchesFormat =
            selectedDocumentFormat === "all" ||
            getDocumentExtension(documentItem.filename) === selectedDocumentFormat

        return matchesKeyword && matchesFormat
    })

    documentCount.textContent = allDocuments.length === filteredDocuments.length
        ? `${allDocuments.length} 个文档`
        : `${filteredDocuments.length} / ${allDocuments.length}`

    if (filteredDocuments.length === 0) {
        const emptyItem = document.createElement("li")
        emptyItem.className = "listPlaceholder"
        emptyItem.textContent = allDocuments.length === 0
            ? "知识库中没有文档"
            : "没有符合当前条件的文档"
        documentList.appendChild(emptyItem)
        return
    }

    for (const documentItem of filteredDocuments) {
        const listItem = document.createElement("li")
        const documentInfo = document.createElement("div")
        const titleRow = document.createElement("div")
        const filename = document.createElement("strong")
        const statusBadge = document.createElement("span")
        const metadata = document.createElement("span")
        const documentActions = document.createElement("div")
        const viewButton = document.createElement("button")
        const deleteButton = currentUser?.role === "admin"
            ? document.createElement("button")
            : null

        listItem.className = "documentItem"
        documentInfo.className = "documentInfo"
        titleRow.className = "documentTitleRow"
        statusBadge.className = "statusBadge"
        metadata.className = "documentMetadata"
        documentActions.className = "documentActions"
        if (deleteButton) {
            deleteButton.className = "dangerButton"
        }

        filename.textContent = documentItem.filename
        filename.title = documentItem.filename
        statusBadge.textContent = "已索引"

        metadata.textContent =
            `${formatFileSize(documentItem.size_bytes)} · ` +
            `${formatDate(documentItem.updated_at)}`

        viewButton.type = "button"
        viewButton.textContent = "查看"
        if (deleteButton) {
            deleteButton.type = "button"
            deleteButton.textContent = "删除"
            deleteButton.disabled = knowledgeOperationRunning
        }

        viewButton.addEventListener("click", function () {
            viewDocument(documentItem.filename)
        })

        if (deleteButton) {
            deleteButton.addEventListener("click", function () {
                deleteDocument(
                    documentItem.filename,
                    deleteButton
                )
            })
        }

        titleRow.append(filename, statusBadge)
        documentInfo.append(titleRow, metadata)
        documentActions.append(viewButton)

        if (deleteButton) {
            documentActions.append(deleteButton)
        }
        listItem.append(documentInfo, documentActions)
        documentList.appendChild(listItem)
    }
}

async function loadDocuments() {
    documentList.replaceChildren()

    try {
        const response = await authenticatedFetch("/knowledge/documents")
        const data = await response.json()

        if (!response.ok) {
            documentCount.textContent = "加载失败"
            documentList.textContent =
                data.detail || "文档列表加载失败"

            return
        }

        allDocuments = data.documents
        renderDocuments()

    } catch (error) {
        console.error(error)
        documentCount.textContent = "加载失败"
        documentList.textContent = "无法获取文档列表"
    }
}

async function viewDocument(filename) {
    documentStatus.textContent = `正在读取 ${filename}……`

    try {
        const response = await authenticatedFetch(
            "/knowledge/documents/" +
            encodeURIComponent(filename)
        )

        const data = await response.json()

        if (!response.ok) {
            documentStatus.textContent =
                data.detail || "文档读取失败"

            return
        }

        openedDocumentName = data.filename
        detailFilename.textContent = data.filename

        detailMetadata.textContent =
            `${formatFileSize(data.size_bytes)} · ` +
            `${formatDate(data.updated_at)}`

        detailContent.textContent = data.content
        renderDocumentChunks(data.chunks || [])
        showDocumentDetailView("original")
        documentDetail.hidden = false
        document.body.style.overflow = "hidden"
        closeDetailButton.focus()
        documentStatus.textContent = ""

    } catch (error) {
        console.error(error)
        documentStatus.textContent = "无法连接到服务器"
    }
}

async function deleteDocument(filename, deleteButton) {
    if (knowledgeOperationRunning) {
        documentStatus.textContent = "知识库正在更新，请稍后再操作"
        return
    }

    const confirmed = window.confirm(
        `确定删除 ${filename} 吗？\n` +
        "删除后知识库会自动重新建库。"
    )

    if (!confirmed) {
        return
    }

    setKnowledgeOperationRunning(true)

    documentStatus.textContent =
        `正在删除 ${filename} 并重新建库……`

    try {
        const response = await authenticatedFetch(
            "/knowledge/documents/" +
            encodeURIComponent(filename),
            {
                method: "DELETE"
            }
        )

        const data = await response.json()

        if (!response.ok) {
            documentStatus.textContent =
                data.detail || "文档删除失败"

            return
        }

        if (openedDocumentName === filename) {
            closeDocumentDetail()
        }

        documentStatus.textContent =
            `${data.filename} 删除成功，` +
            `知识库剩余 ${data.document_count} 个文档`

        await loadDocuments()
        await loadKnowledgeStats()

    } catch (error) {
        console.error(error)
        documentStatus.textContent = "无法连接到服务器"

    } finally {
        setKnowledgeOperationRunning(false)
    }
}

function closeDocumentDetail() {
    openedDocumentName = null
    documentDetail.hidden = true
    document.body.style.overflow = ""
    detailFilename.textContent = "文档详情"
    detailMetadata.textContent = ""
    detailContent.textContent = ""
    detailChunks.replaceChildren()
    detailChunkCount.textContent = "0"
    showDocumentDetailView("original")
}

function selectUploadFile(file) {
    if (!file) {
        selectedUploadFile = null
        selectedFileName.textContent = "暂未选择文件"
        uploadStatus.textContent = "支持 TXT、DOCX 和 PDF 文档，最大 10MB"
        return
    }

    const lowerFilename = file.name.toLowerCase()
    const isSupportedFile =
        lowerFilename.endsWith(".txt") ||
        lowerFilename.endsWith(".docx") ||
        lowerFilename.endsWith(".pdf")

    if (!isSupportedFile) {
        selectedUploadFile = null
        selectedFileName.textContent = "文件格式不支持"
        uploadStatus.textContent = "目前只支持 TXT、DOCX 和 PDF 文件"
        return
    }

    if (file.size > 10 * 1024 * 1024) {
        selectedUploadFile = null
        selectedFileName.textContent = "文件大小超过限制"
        uploadStatus.textContent = "文件大小不能超过 10MB"
        return
    }

    selectedUploadFile = file
    selectedFileName.textContent = file.name

    uploadStatus.textContent =
        `已选择 ${file.name} · ${formatFileSize(file.size)}`
}

async function uploadDocument() {
    if (knowledgeOperationRunning) {
        uploadStatus.textContent = "知识库正在更新，请稍后再上传"
        return
    }

    const file = selectedUploadFile || fileInput.files[0]

    if (!file) {
        uploadStatus.textContent = "请先选择 TXT、DOCX 或 PDF 文件"
        return
    }

    setKnowledgeOperationRunning(true)
    uploadButton.textContent = "正在索引……"
    uploadStatus.textContent = "正在读取并上传文档……"
    renderBuildProgress("running", {
        title: "正在上传并建立索引",
        message: `${file.name} 正在由后端处理，请勿关闭页面`
    })

    try {
        const formData = new FormData()
        formData.append("file", file)
        formData.append(
            "overwrite",
            overwriteInput.checked ? "true" : "false"
        )

        const response = await authenticatedFetch(
            "/knowledge/upload-file",
            {
                method: "POST",
                body: formData
            }
        )

        const data = await response.json()

        if (!response.ok) {
            const errorInfo = getErrorInfo(data, "上传失败")
            uploadStatus.textContent = errorInfo.message
            renderBuildProgress("error", {
                title: "上传或建库失败",
                message: errorInfo.message,
                failedStage: errorInfo.stage
            })

            return
        }

        uploadStatus.textContent =
            `${data.filename} 上传成功 · ` +
            `${data.chunk_count} 个文本片段`
        renderBuildProgress("success", {
            title: "文档已加入知识库",
            message:
                `${data.document_count} 个文档 · ` +
                `${data.chunk_count} 个片段 · ` +
                `${data.vector_count} 个向量`
        })

        selectedUploadFile = null
        fileInput.value = ""
        selectedFileName.textContent = "暂未选择文件"
        overwriteInput.checked = false

        await loadDocuments()
        await loadKnowledgeStats()

    } catch (error) {
        console.error(error)
        uploadStatus.textContent = "无法连接到服务器"
        renderBuildProgress("error", {
            title: "无法连接到服务器",
            message: "请确认FastAPI服务正在运行"
        })

    } finally {
        setKnowledgeOperationRunning(false)
        uploadButton.textContent = "上传并索引"
    }
}

async function rebuildKnowledgeBase() {
    if (knowledgeOperationRunning) {
        documentStatus.textContent = "知识库正在更新，请稍后再操作"
        return
    }

    const confirmed = window.confirm(
        "确定重新生成知识库索引吗？\n" +
        "系统会重新读取所有 TXT、DOCX 和 PDF 文档。"
    )

    if (!confirmed) {
        return
    }

    setKnowledgeOperationRunning(true)
    rebuildButton.textContent = "建库中……"
    documentStatus.textContent = "正在重新读取文档并生成索引……"
    renderBuildProgress("running", {
        title: "正在重新建立知识库",
        message: "后端正在处理全部文档，请勿关闭页面"
    })

    try {
        const response = await authenticatedFetch(
            "/knowledge/rebuild",
            {
                method: "POST"
            }
        )

        const data = await response.json()

        if (!response.ok) {
            const errorInfo = getErrorInfo(data, "重新建库失败")
            documentStatus.textContent = errorInfo.message
            renderBuildProgress("error", {
                title: "重新建库失败",
                message: errorInfo.message,
                failedStage: errorInfo.stage
            })

            return
        }

        documentStatus.textContent =
            `建库成功 · ${data.document_count} 个文档 · ` +
            `${data.vector_count} 个向量`
        renderBuildProgress("success", {
            title: "知识库重建完成",
            message:
                `${data.document_count} 个文档 · ` +
                `${data.chunk_count} 个片段 · ` +
                `${data.vector_count} 个向量`
        })

        await loadDocuments()
        await loadKnowledgeStats()

    } catch (error) {
        console.error(error)
        documentStatus.textContent = "无法连接到服务器"
        renderBuildProgress("error", {
            title: "无法连接到服务器",
            message: "请确认FastAPI服务正在运行"
        })

    } finally {
        setKnowledgeOperationRunning(false)
        rebuildButton.textContent = "重新建库"
    }
}

function resizeQuestionInput() {
    questionInput.style.height = "auto"

    questionInput.style.height =
        `${Math.min(questionInput.scrollHeight, 150)}px`
}

function isConversationDrawerMode() {
    return window.matchMedia("(max-width: 1180px)").matches
}

function isKnowledgeDrawerMode() {
    return window.matchMedia("(max-width: 980px)").matches
}

function closeKnowledgeDrawer() {
    knowledgeSection.classList.remove("isOpen")
    sidebarBackdrop.hidden = true
    document.body.classList.remove("sidebarOpen")
}

function closeConversationDrawer() {
    conversationSidebar.classList.remove("isOpen")
    conversationBackdrop.hidden = true
    document.body.classList.remove("conversationSidebarOpen")
}

function syncSidebarLayout() {
    appShell.classList.toggle(
        "isConversationCollapsed",
        conversationCollapsed
    )
    appShell.classList.toggle(
        "isKnowledgeCollapsed",
        knowledgeCollapsed
    )

    const conversationExpanded = isConversationDrawerMode()
        ? conversationSidebar.classList.contains("isOpen")
        : !conversationCollapsed
    const knowledgeExpanded = isKnowledgeDrawerMode()
        ? knowledgeSection.classList.contains("isOpen")
        : !knowledgeCollapsed

    mobileConversationButton.setAttribute(
        "aria-expanded",
        String(conversationExpanded)
    )
    mobileKnowledgeButton.setAttribute(
        "aria-expanded",
        String(knowledgeExpanded)
    )
    mobileConversationButton.classList.toggle(
        "isActive",
        conversationExpanded
    )
    mobileKnowledgeButton.classList.toggle(
        "isActive",
        knowledgeExpanded
    )
}

function openKnowledgeSidebar() {
    if (isKnowledgeDrawerMode()) {
        closeConversationDrawer()
        knowledgeSection.classList.add("isOpen")
        sidebarBackdrop.hidden = false
        document.body.classList.add("sidebarOpen")
    } else {
        knowledgeCollapsed = false
        localStorage.setItem(
            "knowledgeSidebarCollapsed",
            "false"
        )
    }

    syncSidebarLayout()
}

function closeKnowledgeSidebar() {
    if (isKnowledgeDrawerMode()) {
        closeKnowledgeDrawer()
    } else {
        knowledgeCollapsed = true
        localStorage.setItem(
            "knowledgeSidebarCollapsed",
            "true"
        )
    }

    syncSidebarLayout()
}

function toggleKnowledgeSidebar() {
    const isOpen = isKnowledgeDrawerMode()
        ? knowledgeSection.classList.contains("isOpen")
        : !knowledgeCollapsed

    if (isOpen) {
        closeKnowledgeSidebar()
    } else {
        openKnowledgeSidebar()
    }
}

function openConversationSidebar() {
    if (isConversationDrawerMode()) {
        closeKnowledgeDrawer()
        conversationSidebar.classList.add("isOpen")
        conversationBackdrop.hidden = false
        document.body.classList.add("conversationSidebarOpen")
    } else {
        conversationCollapsed = false
        localStorage.setItem(
            "conversationSidebarCollapsed",
            "false"
        )
    }

    syncSidebarLayout()
}

function closeConversationSidebar() {
    if (isConversationDrawerMode()) {
        closeConversationDrawer()
    } else {
        conversationCollapsed = true
        localStorage.setItem(
            "conversationSidebarCollapsed",
            "true"
        )
    }

    syncSidebarLayout()
}

function toggleConversationSidebar() {
    const isOpen = isConversationDrawerMode()
        ? conversationSidebar.classList.contains("isOpen")
        : !conversationCollapsed

    if (isOpen) {
        closeConversationSidebar()
    } else {
        openConversationSidebar()
    }
}

function handleSidebarResize() {
    if (!isConversationDrawerMode()) {
        closeConversationDrawer()
    }

    if (!isKnowledgeDrawerMode()) {
        closeKnowledgeDrawer()
    }

    syncSidebarLayout()
}

async function sendQuestion() {
    const question = questionInput.value.trim()

    if (!question) {
        answerBox.textContent = "请先输入问题"
        questionInput.focus()
        return
    }

    if (currentConversationId === null) {
        const conversationId = await createConversation()

        if (conversationId === null) {
            answerBox.textContent = "新建会话失败"
            return
        }
    }

    answerBox.textContent = "AI 正在思考……"
    sourcePanel.hidden = true
    showThinkingState(question)

    sendButton.disabled = true
    sendButton.classList.add("isSending")
    sendButtonLabel.textContent = "思考中"

    try {
        const response = await authenticatedFetch(
            "/rag/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question,
                    conversation_id: currentConversationId
                })
            }
        )

        const data = await response.json()

        if (!response.ok) {
            answerBox.textContent =
                data.detail || "请求失败"

            await loadConversationMessages()
            historyStatus.textContent =
                data.detail || "请求失败"

            return
        }

        answerBox.textContent = data.answer
        showSources(data.sources || [])

        questionInput.value = ""
        resizeQuestionInput()

        messagePage = 1
        await loadConversationMessages()
        await loadConversations(false)

    } catch (error) {
        console.error(error)
        answerBox.textContent = "无法连接到服务器"

        await loadConversationMessages()
        historyStatus.textContent = "无法连接到服务器"

    } finally {
        sendButton.disabled = false
        sendButton.classList.remove("isSending")
        sendButtonLabel.textContent = "发送"
        questionInput.focus()
    }
}

sendButton.addEventListener("click", sendQuestion)
loadHistoryButton.addEventListener("click", loadHistory)
newConversationButton.addEventListener(
    "click",
    createConversation
)
loadMoreConversationsButton.addEventListener(
    "click",
    loadMoreConversations
)
loadOlderMessagesButton.addEventListener(
    "click",
    loadOlderMessages
)
uploadButton.addEventListener("click", uploadDocument)
rebuildButton.addEventListener("click", rebuildKnowledgeBase)
closeDetailButton.addEventListener("click", closeDocumentDetail)
originalTextTab.addEventListener("click", function () {
    showDocumentDetailView("original")
})
documentChunksTab.addEventListener("click", function () {
    showDocumentDetailView("chunks")
})

documentDetail.addEventListener("click", function (event) {
    if (event.target === documentDetail) {
        closeDocumentDetail()
    }
})

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !documentDetail.hidden) {
        closeDocumentDetail()
    }
})

mobileKnowledgeButton.addEventListener(
    "click",
    toggleKnowledgeSidebar
)

closeKnowledgeButton.addEventListener(
    "click",
    closeKnowledgeSidebar
)

sidebarBackdrop.addEventListener(
    "click",
    closeKnowledgeSidebar
)

mobileConversationButton.addEventListener(
    "click",
    toggleConversationSidebar
)

closeConversationButton.addEventListener(
    "click",
    closeConversationSidebar
)

conversationBackdrop.addEventListener(
    "click",
    closeConversationSidebar
)

loginTabButton.addEventListener("click", function () {
    setAuthMode("login")
})

registerTabButton.addEventListener("click", function () {
    setAuthMode("register")
})

authForm.addEventListener("submit", submitAuthForm)

logoutButton.addEventListener("click", function () {
    const confirmed = window.confirm(
        "确定要退出当前账号吗？"
    )

    if (!confirmed) {
        return
    }

    showAuthScreen("你已安全退出")
})

questionInput.addEventListener("input", resizeQuestionInput)

questionInput.addEventListener("keydown", function (event) {
    if (
        event.key === "Enter"
        && !event.shiftKey
        && !event.isComposing
    ) {
        event.preventDefault()

        if (!sendButton.disabled) {
            sendQuestion()
        }
    }
})

fileInput.addEventListener("change", function () {
    selectUploadFile(fileInput.files[0])
})

for (const eventName of ["dragenter", "dragover"]) {
    dropZone.addEventListener(eventName, function (event) {
        event.preventDefault()
        dropZone.classList.add("isDragging")
    })
}

for (const eventName of ["dragleave", "drop"]) {
    dropZone.addEventListener(eventName, function (event) {
        event.preventDefault()
        dropZone.classList.remove("isDragging")
    })
}

dropZone.addEventListener("drop", function (event) {
    const file = event.dataTransfer.files[0]
    selectUploadFile(file)
})

documentSearchInput.addEventListener("input", renderDocuments)

for (const formatButton of documentFormatButtons) {
    formatButton.addEventListener("click", function () {
        selectedDocumentFormat = formatButton.dataset.format

        for (const button of documentFormatButtons) {
            button.classList.toggle(
                "isActive",
                button === formatButton
            )
        }

        renderDocuments()
    })
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        if (isKnowledgeDrawerMode()) {
            closeKnowledgeSidebar()
        }

        if (isConversationDrawerMode()) {
            closeConversationSidebar()
        }
    }
})

window.addEventListener(
    "resize",
    handleSidebarResize
)

async function initializeApplication() {
    syncSidebarLayout()
    resizeQuestionInput()
    await Promise.all([
        loadModelInfo(),
        loadHistory(),
        loadDocuments(),
        loadKnowledgeStats()
    ])
}

setAuthMode("login")
restoreSession()
