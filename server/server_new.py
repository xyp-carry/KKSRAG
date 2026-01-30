import streamlit as st
from jinja2 import Template

# 1. 定义全屏 CSS
fullscreen_css = """
<style>
    .stApp { background-color: white; } /* 可选：修改背景色 */
    /* 隐藏 Streamlit 默认的顶部和底部 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 强制主容器全屏无边距 */
    .main .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    
    /* 你的 HTML 容器需要 100vh 高度 */
    .my-fullscreen-html {
        height: 100vh;
        width: 100%;
        overflow: auto; /* 如果内容溢出，允许滚动 */
    }
</style>
"""

# 2. 读取并渲染你的 HTML (假设里面有 JS 动画)
with open('./KnowledgeServer.html', 'r', encoding='utf-8') as f:
    # 为了撑满全屏，你可能需要在你的 HTML 文件最外层包裹一个 div class="my-fullscreen-html"
    # 或者在这里直接包裹：
    raw_html = f.read()
    wrapped_html = f'<div class="my-fullscreen-html">{raw_html}</div>'

# 3. 注入 CSS 和 HTML
st.markdown(fullscreen_css, unsafe_allow_html=True)
st.markdown(wrapped_html, unsafe_allow_html=True)
