import { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface MathRendererProps {
  content: string;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * MathRenderer 组件
 * 用于渲染包含 LaTeX 数学公式的文本
 * 支持 $...$ 行内公式和 $$...$$ 块级公式
 */
/**
 * 还原 JSON 转义字符
 * 处理后端传输过程中被 JSON 序列化转义的字符
 */
function unescapeText(text: string): string {
  return text
    // 引号
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    // 空白字符
    .replace(/\\n/g, '\n')
    .replace(/\\t/g, '\t')
    .replace(/\\r/g, '\r')
    // 括号
    .replace(/\\\(/g, '(')
    .replace(/\\\)/g, ')')
    .replace(/\\\[/g, '[')
    .replace(/\\\]/g, ']')
    .replace(/\\\{/g, '{')
    .replace(/\\\}/g, '}')
    // 反斜杠（必须放在最后）
    .replace(/\\\\/g, '\\');
}

/**
 * 自动检测并包裹 LaTeX 公式
 * 改进：智能处理混合内容（中文+LaTeX）
 */
function autoWrapLatex(text: string): string {
  if (!text) return text;
  
  const textStr = String(text).trim();
  
  // 如果已经有 $ 符号，说明已经包裹过了，直接返回
  if (textStr.includes('$')) {
    return textStr;
  }
  
  // 检测是否包含 LaTeX 命令
  const hasLatexCommands = /\\[a-zA-Z]+/.test(textStr);
  
  if (!hasLatexCommands) {
    return textStr;  // 没有 LaTeX 命令，直接返回
  }
  
  // 检测是否包含中文或其他文本（混合内容）
  const hasChinese = /[\u4e00-\u9fa5]/.test(textStr);
  
  // 如果是混合内容（有中文文本 + LaTeX），不做整体包裹
  // 保持原样，让后端或用户自己用 $ 标记 LaTeX 部分
  if (hasChinese) {
    return textStr;
  }
  
  // 纯 LaTeX 内容，整体包裹为行内公式
  return `$${textStr}$`;
}

export default function MathRenderer({ content, className, style }: MathRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return '';
    
    // 重要：先自动包裹 LaTeX（在 unescape 之前）
    let result = autoWrapLatex(content);
    
    // 只对非 LaTeX 部分进行 unescape
    // 如果已经包裹了 $，说明是 LaTeX，要小心处理
    const hasLatex = result.includes('$');
    if (!hasLatex) {
      // 没有 LaTeX，安全地进行 unescape
      result = unescapeText(result);
    }
    // 如果有 LaTeX，保持原样，不做 unescape（避免破坏 LaTeX 命令）
    
    // 1. 先处理块级公式 $$...$$ (内部换行符由 KaTeX 处理)
    result = result.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
      try {
        return `<div class="katex-block" style="text-align: center; margin: 12px 0;">${katex.renderToString(formula.trim(), { 
          displayMode: true, 
          throwOnError: false,
          strict: false  // 放宽严格模式，更宽容地处理格式问题
        })}</div>`;
      } catch (e) {
        console.error('KaTeX 块级公式渲染失败:', e);
        return `<code style="color: #d32f2f;" title="LaTeX渲染失败: ${e}">${formula}</code>`;
      }
    });

    // 2. 再处理行内公式 $...$
    result = result.replace(/\$([^$\n]+?)\$/g, (_, formula) => {
      try {
        return katex.renderToString(formula.trim(), { 
          displayMode: false, 
          throwOnError: false,
          strict: false  // 放宽严格模式
        });
      } catch (e) {
        console.error('KaTeX 行内公式渲染失败:', e);
        return `<code style="color: #d32f2f;" title="LaTeX渲染失败: ${e}">${formula}</code>`;
      }
    });

    // 3. 最后处理换行符（避免替换 HTML 标签属性内的换行符）
    // 使用更安全的方式：只替换不在 < > 标签内的换行符
    result = result.replace(/\n(?![^<]*>)/g, '<br>');

    return result;
  }, [content]);

  return (
    <div 
      className={className}
      style={{ lineHeight: 1.8, ...style }}
      dangerouslySetInnerHTML={{ __html: rendered }} 
    />
  );
}

