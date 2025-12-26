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

export default function MathRenderer({ content, className, style }: MathRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return '';
    
    // 0. 先过滤转义字符
    let result = unescapeText(content);
    
    // 1. 先处理块级公式 $$...$$ (内部换行符由 KaTeX 处理)
    result = result.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
      try {
        return `<div class="katex-block" style="text-align: center; margin: 12px 0;">${katex.renderToString(formula.trim(), { 
          displayMode: true, 
          throwOnError: false 
        })}</div>`;
      } catch {
        return `<code style="color: #d32f2f;">${formula}</code>`;
      }
    });

    // 2. 再处理行内公式 $...$
    result = result.replace(/\$([^$\n]+?)\$/g, (_, formula) => {
      try {
        return katex.renderToString(formula.trim(), { 
          displayMode: false, 
          throwOnError: false 
        });
      } catch {
        return `<code style="color: #d32f2f;">${formula}</code>`;
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

