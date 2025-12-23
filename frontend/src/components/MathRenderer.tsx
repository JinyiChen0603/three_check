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
export default function MathRenderer({ content, className, style }: MathRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return '';
    
    // 先处理换行符，将 \n 转换为 <br>
    let result = content.replace(/\n/g, '<br>');
    
    // 处理块级公式 $$...$$
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

    // 处理行内公式 $...$（注意避免匹配已经处理过的块级公式）
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

