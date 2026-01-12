/**
 * LaTeX环境预处理工具
 * 将LaTeX环境和命令转换为HTML，以便在Web页面中正确显示
 */

/**
 * 预处理LaTeX环境和命令，转换为HTML
 * @param content 原始内容
 * @returns 处理后的HTML内容
 */
export function preprocessLatexEnvironments(content: string): string {
  if (!content) return '';
  
  try {
    let result = content;
    
    // 1. 处理 itemize 环境（无序列表）
    result = result.replace(/\\begin\{itemize\}([\s\S]*?)\\end\{itemize\}/g, (match, items) => {
      const itemList = items.match(/\\item\s+([^\n]*(?:\n(?!\\item)[^\n]*)*)/g);
      if (itemList) {
        const htmlItems = itemList.map((item: string) => {
          const text = item.replace(/\\item\s+/, '').trim();
          return `<li>${text}</li>`;
        }).join('\n');
        return `<ul class="latex-list">${htmlItems}</ul>`;
      }
      return match;
    });
    
    // 2. 处理 enumerate 环境（有序列表）
    result = result.replace(/\\begin\{enumerate\}([\s\S]*?)\\end\{enumerate\}/g, (match, items) => {
      const itemList = items.match(/\\item\s+([^\n]*(?:\n(?!\\item)[^\n]*)*)/g);
      if (itemList) {
        const htmlItems = itemList.map((item: string) => {
          const text = item.replace(/\\item\s+/, '').trim();
          return `<li>${text}</li>`;
        }).join('\n');
        return `<ol class="latex-list">${htmlItems}</ol>`;
      }
      return match;
    });
    
    // 3. 处理文本格式命令
    result = result.replace(/\\textbf\{([^}]+)\}/g, '<strong>$1</strong>');
    result = result.replace(/\\textit\{([^}]+)\}/g, '<em>$1</em>');
    result = result.replace(/\\emph\{([^}]+)\}/g, '<em>$1</em>');
    result = result.replace(/\\textsc\{([^}]+)\}/g, '<span style="font-variant: small-caps;">$1</span>');
    result = result.replace(/\\underline\{([^}]+)\}/g, '<u>$1</u>');
    result = result.replace(/\\texttt\{([^}]+)\}/g, '<code class="latex-code">$1</code>');
    
    // 4. 处理间距命令
    result = result.replace(/\\medskip/g, '<div class="latex-medskip"></div>');
    result = result.replace(/\\bigskip/g, '<div class="latex-bigskip"></div>');
    result = result.replace(/\\smallskip/g, '<div class="latex-smallskip"></div>');
    result = result.replace(/\\vspace\{[^}]+\}/g, '<div class="latex-vspace"></div>');
    result = result.replace(/\\hspace\{[^}]+\}/g, '<span class="latex-hspace"></span>');
    
    // 5. 处理换行和段落
    result = result.replace(/\\newline/g, '<br>');
    result = result.replace(/\\\\\s*(?![a-zA-Z])/g, '<br>'); // \\ 但后面不跟字母
    result = result.replace(/\\noindent/g, '');
    result = result.replace(/\\par\s*/g, '</p><p>');
    
    // 6. 处理章节标题
    result = result.replace(/\\section\*?\{([^}]+)\}/g, '<h2 class="latex-section">$1</h2>');
    result = result.replace(/\\subsection\*?\{([^}]+)\}/g, '<h3 class="latex-subsection">$1</h3>');
    result = result.replace(/\\subsubsection\*?\{([^}]+)\}/g, '<h4 class="latex-subsubsection">$1</h4>');
    
    // 7. 处理特殊符号
    result = result.replace(/\\dots/g, '…');
    result = result.replace(/\\ldots/g, '…');
    result = result.replace(/\\cdots/g, '⋯');
    result = result.replace(/---/g, '—'); // em dash
    result = result.replace(/--/g, '–'); // en dash
    
    // 8. 处理转义字符
    result = result.replace(/\\_/g, '_');
    result = result.replace(/\\&/g, '&');
    result = result.replace(/\\%/g, '%');
    result = result.replace(/\\#/g, '#');
    result = result.replace(/\\\$/g, '$');
    result = result.replace(/\\{/g, '{');
    result = result.replace(/\\}/g, '}');
    
    // 9. 处理引号
    result = result.replace(/``/g, '"'); // 左双引号
    result = result.replace(/''/g, '"'); // 右双引号
    result = result.replace(/`/g, "'"); // 左单引号
    
    // 10. 处理其他常见命令
    result = result.replace(/\\quad/g, '<span class="latex-quad"></span>');
    result = result.replace(/\\qquad/g, '<span class="latex-qquad"></span>');
    
    return result;
  } catch (error) {
    console.warn('LaTeX环境预处理出错，返回原内容:', error);
    return content;
  }
}

/**
 * 处理段落和换行
 * @param content 内容
 * @returns 处理后的内容
 */
export function processParagraphs(content: string): string {
  if (!content) return '';
  
  // 将双换行转换为段落分隔
  let result = content.replace(/\n\n+/g, '</p><p>');
  
  // 将单换行转换为 <br>（但不影响已经在HTML标签内的内容）
  result = result.replace(/\n(?![^<]*>)/g, '<br>');
  
  // 包裹在段落标签中
  if (!result.startsWith('<p>')) {
    result = '<p>' + result;
  }
  if (!result.endsWith('</p>')) {
    result = result + '</p>';
  }
  
  return result;
}
