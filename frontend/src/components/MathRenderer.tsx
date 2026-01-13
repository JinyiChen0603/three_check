import { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { preprocessLatexEnvironments } from '../utils/latexPreprocessor';

interface MathRendererProps {
  content: string;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * MathRenderer 组件（增强版 - 高宽容度）
 * 
 * 功能：
 * - 自动识别并包装数学表达式（高宽容度模式）
 * - 支持LaTeX环境（itemize, enumerate等）
 * - 支持LaTeX文本格式命令（\textbf, \textit等）
 * - 支持数学公式渲染（行内和块级）
 * - 自动检测并包装孤立的 LaTeX 数学命令
 * - 自动处理换行和段落
 * 
 * 渲染流程：
 * 0a. 自动识别不规范的数学表达式（如裸露的下标、上标）
 * 0b. 自动检测孤立的 LaTeX 命令（如 \boxed, \frac, \arctan 等）并包装为数学公式
 * 1. 预处理LaTeX环境和命令 → HTML（包含自动包装）
 * 2. 处理块级公式 \[...\] 和 $$...$$ → KaTeX displayMode
 * 3. 处理行内公式 \(...\) 和 $...$ → KaTeX inline
 * 4. 处理段落和换行符
 * 
 * 支持的数学公式定界符：
 * - 块级公式：\[...\] 或 $$...$$
 * - 行内公式：\(...\) 或 $...$
 * - 自动检测：下标(_)、上标(^)、LaTeX命令等
 */
export default function MathRenderer({ content, className, style }: MathRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return '';
    
    let result = String(content);
    
    // 步骤0: 自动检测并包装孤立的 LaTeX 数学命令
    // 保护已经在数学模式中的内容（使用占位符）
    const mathBlocks: string[] = [];
    let blockIndex = 0;
    
    // 保护 $$...$$ 块
    result = result.replace(/\$\$([\s\S]+?)\$\$/g, (match) => {
      const placeholder = `___MATH_BLOCK_${blockIndex}___`;
      mathBlocks[blockIndex++] = match;
      return placeholder;
    });
    
    // 保护 \[...\] 块
    result = result.replace(/\\\[([\s\S]+?)\\\]/g, (match) => {
      const placeholder = `___MATH_BLOCK_${blockIndex}___`;
      mathBlocks[blockIndex++] = match;
      return placeholder;
    });
    
    // 保护 $...$ 行内公式
    result = result.replace(/\$([^$\n]+?)\$/g, (match) => {
      const placeholder = `___MATH_BLOCK_${blockIndex}___`;
      mathBlocks[blockIndex++] = match;
      return placeholder;
    });
    
    // 保护 \(...\) 行内公式
    result = result.replace(/\\\(([^)]+?)\\\)/g, (match) => {
      const placeholder = `___MATH_BLOCK_${blockIndex}___`;
      mathBlocks[blockIndex++] = match;
      return placeholder;
    });
    
    // 检测并包装孤立的 LaTeX 命令
    // 1. 检测以 \boxed 开头的表达式（独立行或片段）
    result = result.replace(/(?:^|[\s\n])(\\boxed\{(?:[^{}]|\{[^{}]*\})*\})(?=[\s\n]|$)/gm, (match, boxed) => {
      return match.replace(boxed, `$${boxed}$`);
    });
    
    // 2. 检测包含多个常见 LaTeX 数学命令的行（如 \dfrac, \frac, \left, \right, \arctan 等）
    // 这些行很可能是数学表达式但没有被定界符包围
    const mathCommandPattern = /^[\s]*\\(?:boxed|frac|dfrac|tfrac|cfrac|sqrt|arctan|arcsin|arccos|arcsinh|arccosh|arctanh|sin|cos|tan|cot|sec|csc|ln|log|exp|lim|sum|prod|int|oint|partial|nabla|infty|pm|mp|times|div|cdot|leq|geq|neq|approx|equiv|left|right|big|Big|bigg|Bigg)\b/;
    
    result = result.split('\n').map(line => {
      // 跳过占位符行
      if (line.includes('___MATH_BLOCK_')) return line;
      // 跳过 HTML 标签行
      if (line.trim().startsWith('<') || line.trim().endsWith('>')) return line;
      // 跳过已经在数学模式的行
      if (line.includes('$') || line.includes('\\[') || line.includes('\\(')) return line;
      
      // 如果行包含数学命令且不在数学模式中，包装它
      if (mathCommandPattern.test(line.trim())) {
        return `$${line.trim()}$`;
      }
      
      // 检测行内是否有未包装的 LaTeX 命令序列
      // 例如: \arctan\left(\dfrac{\sqrt{3}}{3}\right)
      const inlineMathPattern = /\\(?:arctan|arcsin|arccos|sin|cos|tan|ln|log|exp|sqrt|frac|dfrac|left|right)\b[^$\n]*?(?:\{[^}]*\}|\([^)]*\))+/g;
      if (inlineMathPattern.test(line) && !line.includes('$') && !line.includes('\\[')) {
        return line.replace(inlineMathPattern, (match) => `$${match}$`);
      }
      
      return line;
    }).join('\n');
    
    // 恢复保护的数学块
    for (let i = 0; i < mathBlocks.length; i++) {
      result = result.replace(`___MATH_BLOCK_${i}___`, mathBlocks[i]);
    }
    
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

    // 步骤2c: 处理跨行的独立 $ 公式（作为块级公式显示）
    // 匹配独立成行或跨行的 $...$ 公式
    result = result.replace(/(?:^|\n)\s*\$\s*\n([\s\S]+?)\n\s*\$\s*(?:\n|$)/gm, (_, formula) => {
      try {
        return `<div class="katex-block" style="text-align: center; margin: 12px 0;">${katex.renderToString(formula.trim(), { 
          displayMode: true, 
          throwOnError: false,
          strict: false
        })}</div>`;
      } catch (e) {
        console.error('KaTeX 跨行块级公式渲染失败:', formula, e);
        return `<div style="color: #d32f2f; text-align: center; margin: 12px 0;"><code title="LaTeX渲染失败: ${e}">$${formula}$</code></div>`;
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

