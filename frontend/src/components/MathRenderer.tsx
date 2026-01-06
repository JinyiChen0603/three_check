import { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface MathRendererProps {
  content: string;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * MathRenderer 组件（简化版）
 * 
 * 前置条件：
 * - 输入数据为规范的文本格式
 * - 行内公式已用 $ 包裹
 * - 块级公式已用 $$ 包裹
 * - 包裹内都是 LaTeX 标准格式
 * 
 * 渲染逻辑：
 * 1. 处理块级公式 $$...$$ → KaTeX displayMode
 * 2. 处理行内公式 $...$ → KaTeX inline
 * 3. 处理换行符 \n → <br>
 */
export default function MathRenderer({ content, className, style }: MathRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return '';
    
    let result = String(content);
    
    // 1. 处理块级公式 $$...$$ (使用非贪婪匹配，支持多行)
    result = result.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
      try {
        return `<div class="katex-block" style="text-align: center; margin: 12px 0;">${katex.renderToString(formula.trim(), { 
          displayMode: true, 
          throwOnError: false,
          strict: false
        })}</div>`;
      } catch (e) {
        console.error('KaTeX 块级公式渲染失败:', formula, e);
        return `<div style="color: #d32f2f; text-align: center; margin: 12px 0;"><code title="LaTeX渲染失败: ${e}">$$${formula}$$</code></div>`;
      }
    });

    // 2. 处理行内公式 $...$（不跨行）
    result = result.replace(/\$([^$\n]+?)\$/g, (_, formula) => {
      try {
        return katex.renderToString(formula.trim(), { 
          displayMode: false, 
          throwOnError: false,
          strict: false
        });
      } catch (e) {
        console.error('KaTeX 行内公式渲染失败:', formula, e);
        return `<code style="color: #d32f2f;" title="LaTeX渲染失败: ${e}">$${formula}$</code>`;
      }
    });

    // 3. 处理换行符（只替换不在 HTML 标签内的换行符）
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

