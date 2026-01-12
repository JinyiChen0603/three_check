import { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { preprocessLatexEnvironments, processParagraphs } from '../utils/latexPreprocessor';

interface MathRendererProps {
  content: string;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * MathRenderer 组件（增强版）
 * 
 * 功能：
 * - 支持LaTeX环境（itemize, enumerate等）
 * - 支持LaTeX文本格式命令（\textbf, \textit等）
 * - 支持数学公式渲染（行内和块级）
 * - 自动处理换行和段落
 * 
 * 渲染流程：
 * 1. 预处理LaTeX环境和命令 → HTML
 * 2. 处理块级公式 \[...\] 和 $$...$$ → KaTeX displayMode
 * 3. 处理行内公式 \(...\) 和 $...$ → KaTeX inline
 * 4. 处理段落和换行符
 * 
 * 支持的数学公式定界符：
 * - 块级公式：\[...\] 或 $$...$$
 * - 行内公式：\(...\) 或 $...$
 */
export default function MathRenderer({ content, className, style }: MathRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return '';
    
    let result = String(content);
    
    // 步骤1: 预处理LaTeX环境（列表、格式等）
    result = preprocessLatexEnvironments(result);
    
    // 步骤2a: 先处理 LaTeX 原生块级公式 \[...\] (支持多行)
    result = result.replace(/\\\[([\s\S]+?)\\\]/g, (_, formula) => {
      try {
        return `<div class="katex-block" style="text-align: center; margin: 12px 0;">${katex.renderToString(formula.trim(), { 
          displayMode: true, 
          throwOnError: false,
          strict: false
        })}</div>`;
      } catch (e) {
        console.error('KaTeX 块级公式渲染失败 (\\[...\\]):', formula, e);
        return `<div style="color: #d32f2f; text-align: center; margin: 12px 0;"><code title="LaTeX渲染失败: ${e}">\\[${formula}\\]</code></div>`;
      }
    });
    
    // 步骤2b: 处理 $$ 块级公式 $$...$$ (使用非贪婪匹配，支持多行)
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

    // 步骤3a: 先处理 LaTeX 原生行内公式 \(...\)（不跨行）
    result = result.replace(/\\\(([^)]+?)\\\)/g, (_, formula) => {
      try {
        return katex.renderToString(formula.trim(), { 
          displayMode: false, 
          throwOnError: false,
          strict: false
        });
      } catch (e) {
        console.error('KaTeX 行内公式渲染失败 (\\(...\\)):', formula, e);
        return `<code style="color: #d32f2f;" title="LaTeX渲染失败: ${e}">\\(${formula}\\)</code>`;
      }
    });
    
    // 步骤3b: 处理 $ 行内公式 $...$（不跨行）
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

    // 步骤4: 处理段落和换行（如果内容中没有HTML标签）
    if (!result.includes('<ul') && !result.includes('<ol') && !result.includes('<h')) {
      // 将双换行转换为段落
      result = result.replace(/\n\n+/g, '</p><p>');
      // 将单换行转换为 <br>（只替换不在 HTML 标签内的换行符）
      result = result.replace(/\n(?![^<]*>)/g, '<br>');
      // 包裹段落标签
      if (!result.startsWith('<p>') && !result.startsWith('<div') && !result.startsWith('<ul') && !result.startsWith('<ol')) {
        result = '<p>' + result + '</p>';
      }
    } else {
      // 如果已经有HTML结构，只处理剩余的换行
      result = result.replace(/\n(?![^<]*>)/g, '<br>');
    }

    return result;
  }, [content]);

  return (
    <div 
      className={`math-content ${className || ''}`}
      style={{ lineHeight: 1.8, wordWrap: 'break-word', ...style }}
      dangerouslySetInnerHTML={{ __html: rendered }} 
    />
  );
}

