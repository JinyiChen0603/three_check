/**
 * LaTeX环境预处理工具
 * 将LaTeX环境和命令转换为HTML，以便在Web页面中正确显示
 */

/**
 * 自动包装可能的数学表达式
 * 检测包含下标、上标、特殊符号的文本并自动添加 $ 包围
 */
export function autoWrapMathExpressions(content: string): string {
  if (!content) return '';
  
  let result = content;
  
  // 保护已经在数学模式中的内容
  const protectedBlocks: string[] = [];
  let blockIndex = 0;
  
  // 保护所有已有的数学定界符内容
  result = result.replace(/\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\$[^$\n]+?\$|\\\([^)]+?\\\)/g, (match) => {
    const placeholder = `___PROTECTED_${blockIndex}___`;
    protectedBlocks[blockIndex++] = match;
    return placeholder;
  });
  
  // 1. 检测并包装含有下标的表达式（如 v_1, S_A, w_B）
  // 匹配模式：字母后跟 _{ 或 _ 加字母/数字
  result = result.replace(/\b([a-zA-Z]+)_\{([^}]+)\}/g, '$$$1_{$2}$$');
  result = result.replace(/\b([a-zA-Z]+)_([a-zA-Z0-9]+)\b/g, '$$$1_$2$$');
  
  // 2. 检测并包装含有上标的表达式（如 x^2, y^2）
  result = result.replace(/\b([a-zA-Z]+)\^\{([^}]+)\}/g, '$$$1^{$2}$$');
  result = result.replace(/\b([a-zA-Z]+)\^([0-9]+)\b/g, '$$$1^$2$$');
  
  // 3. 检测复合表达式（如 x^2+y^2=1）
  // 匹配包含 +, -, =, < , >, \le, \ge 等运算符的表达式
  result = result.replace(/([a-zA-Z_\^\{\}0-9]+)\s*([+\-=<>]|\\le|\\ge|\\geq|\\leq|\\neq|\\times|\\cdot)\s*([a-zA-Z_\^\{\}0-9]+)/g, 
    (match, left, op, right) => {
      // 如果已经在 $ 中，不再包装
      if (match.includes('$')) return match;
      return `$${left}${op}${right}$`;
    }
  );
  
  // 3a. 检测连续的数学表达式（如 "x 2 +y 2 =1" - 有空格的情况）
  // 先修正常见的空格问题：x 2 -> x^2, v 1 -> v_1
  result = result.replace(/\b([a-zA-Z])\s+([0-9])\b/g, (match, letter, num) => {
    // 检查前后文，判断是上标还是下标
    // 如果前面有 v, w, S, C 等，通常是下标
    if (['v', 'w', 'S', 'C', 's', 'c'].includes(letter)) {
      return `${letter}_${num}`;
    }
    // 如果是 x, y, z, n, m 等，通常是上标
    if (['x', 'y', 'z', 'n', 'm', 'a', 'b', 'r'].includes(letter)) {
      return `${letter}^${num}`;
    }
    return match;
  });
  
  // 4. 将常见的省略号转换为LaTeX格式
  result = result.replace(/\.\.\./g, '\\ldots');
  result = result.replace(/…/g, '\\ldots');
  result = result.replace(/⋯/g, '\\cdots');
  
  // 5. 检测集合表示（如 V={v_1, v_2, ..., v_6} 或 [1,2]）
  // 包括可能包含 \ldots 的情况
  result = result.replace(/([A-Z][a-zA-Z]*)\s*=\s*\{([^}]+)\}/g, (match) => {
    if (match.includes('$')) return match;
    // 替换花括号为 LaTeX 转义版本
    return match.replace(/\{/g, '\\{').replace(/\}/g, '\\}').replace(/^/, '$').replace(/$/, '$');
  });
  
  // 6. 检测区间表示（如 [1,2]、(0,1) 等，但要避免普通的列表）
  // 如果前后有数学上下文，包装它
  result = result.replace(/([a-zA-Z_0-9]+\s+)?\\in\s+\[([0-9]+),\s*([0-9]+)\]/g, (match) => {
    if (match.includes('$')) return match;
    return `$${match}$`;
  });
  result = result.replace(/\[([0-9]+),\s*([0-9]+)\](?=\s|$|,|\))/g, (match, start, end) => {
    if (match.includes('$')) return match;
    return `$[${start},${end}]$`;
  });
  
  // 7. 将常见的 Unicode 数学符号转换为 LaTeX
  const unicodeToLatex: Record<string, string> = {
    '≤': '\\leq',
    '≥': '\\geq',
    '≠': '\\neq',
    '≈': '\\approx',
    '∈': '\\in',
    '∉': '\\notin',
    '⊂': '\\subset',
    '⊃': '\\supset',
    '⊆': '\\subseteq',
    '⊇': '\\supseteq',
    '∩': '\\cap',
    '∪': '\\cup',
    '∅': '\\emptyset',
    '∞': '\\infty',
    '∀': '\\forall',
    '∃': '\\exists',
    '∇': '\\nabla',
    '∂': '\\partial',
    '→': '\\rightarrow',
    '←': '\\leftarrow',
    '⇒': '\\Rightarrow',
    '⇐': '\\Leftarrow',
    '↔': '\\leftrightarrow',
    '⇔': '\\Leftrightarrow',
    '×': '\\times',
    '÷': '\\div',
    '±': '\\pm',
    '·': '\\cdot',
  };
  
  for (const [unicode, latex] of Object.entries(unicodeToLatex)) {
    result = result.replace(new RegExp(unicode, 'g'), latex);
  }
  
  // 8. 检测 LaTeX 特殊命令（如 \mathcal{C}, \alpha, \ldots）
  // 包括可能有下标的情况，如 \mathcal{C}_A
  result = result.replace(/\\(mathcal|mathbb|mathbf|mathrm|text|alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|ldots|cdots|dots|in|notin|subset|subseteq|supset|supseteq|cap|cup|emptyset|varnothing|infty|forall|exists|nabla|partial|rightarrow|leftarrow|Rightarrow|Leftarrow|leftrightarrow|Leftrightarrow|mapsto|to|ge|le|geq|leq|neq|approx|equiv|sim|simeq|cong|propto|times|div|pm|mp|cdot|circ|bullet|ast|star|dagger|ddagger|vee|wedge|oplus|ominus|otimes|oslash|odot|sum|prod|coprod|int|oint|iint|iiint|sin|cos|tan|cot|sec|csc|arcsin|arccos|arctan|sinh|cosh|tanh|ln|log|exp|lim|max|min|sup|inf|det|dim|ker|deg|gcd|lcm)\b(\{[^}]*\})?(_\{[^}]*\}|_[a-zA-Z0-9]+|\^\{[^}]*\}|\^[a-zA-Z0-9]+)?/g,
    (match) => {
      if (match.startsWith('___PROTECTED_')) return match;
      return match.includes('$') ? match : `$${match}$`;
    }
  );
  
  // 8a. 检测函数调用模式（如 \mathcal{A}(\mathcal{C}_A) 或 A(C)）
  result = result.replace(/([a-zA-Z\\][a-zA-Z_\{\}\\]*)\(([^\)]+)\)/g, (match, func, args) => {
    // 如果包含 LaTeX 命令或下标上标，很可能是数学函数
    if ((func.includes('\\') || func.includes('_') || func.includes('^') || 
         args.includes('\\') || args.includes('_') || args.includes('^')) && !match.includes('$')) {
      return `$${match}$`;
    }
    return match;
  });
  
  // 9. 检测花括号表示的集合（可能没有等号，如独立的 {1, 2, 3}）
  result = result.replace(/\{([a-zA-Z0-9_,\s\.\^\{\}\\]+)\}/g, (match, inner) => {
    // 如果包含LaTeX命令或下标上标，很可能是数学内容
    if (inner.match(/[_\^\\]/) && !match.includes('$')) {
      return `$\\{${inner}\\}$`;
    }
    return match;
  });
  
  // 10. 检测包含多个数学符号的短语（如 "w_A \cdot \mathcal{A}(\mathcal{C}_A)"）
  // 如果一行中有多个数学相关的模式，整行包装
  const lines = result.split('\n');
  result = lines.map(line => {
    if (line.includes('___PROTECTED_')) return line;
    if (line.includes('<')) return line; // 跳过HTML标签
    
    // 统计数学标记出现次数
    const mathMarkers = (line.match(/[_\^]|\\[a-zA-Z]+/g) || []).length;
    const hasOperators = /[+\-=<>]|\\(le|ge|leq|geq|neq|times|cdot|div|pm|mp)/.test(line);
    
    // 如果有3个以上的数学标记，或有运算符且有数学标记，包装整行
    if ((mathMarkers >= 3 || (mathMarkers >= 1 && hasOperators)) && !line.includes('$')) {
      // 但如果行太长（超过100字符），只包装特定部分
      if (line.length > 100) return line;
      return `$${line.trim()}$`;
    }
    return line;
  }).join('\n');
  
  // 11. 合并相邻的数学模式（避免 $x$ $+$ $y$ 这种情况）
  // 多次运行以处理多个相邻的情况
  for (let i = 0; i < 3; i++) {
    result = result.replace(/\$([^$\n]+)\$\s*\$([^$\n]+)\$/g, '$$$1 $2$$');
  }
  
  // 恢复保护的内容
  for (let i = 0; i < protectedBlocks.length; i++) {
    result = result.replace(`___PROTECTED_${i}___`, protectedBlocks[i]);
  }
  
  return result;
}

/**
 * 预处理LaTeX环境和命令，转换为HTML
 * @param content 原始内容
 * @returns 处理后的HTML内容
 */
export function preprocessLatexEnvironments(content: string): string {
  if (!content) return '';
  
  try {
    // 首先进行自动数学表达式包装
    let result = autoWrapMathExpressions(content);
    
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
    
    // 7. 处理特殊符号（注意：\ldots, \cdots 已在自动包装中处理，这里不再转换）
    // result = result.replace(/\\dots/g, '…');
    // result = result.replace(/\\ldots/g, '…');
    // result = result.replace(/\\cdots/g, '⋯');
    result = result.replace(/---/g, '—'); // em dash
    result = result.replace(/--/g, '–'); // en dash
    
    // 8. 处理转义字符（但不处理数学模式中的 \{ 和 \}）
    // 保护数学模式中的内容
    const mathProtected: string[] = [];
    let mathIndex = 0;
    
    result = result.replace(/\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\$[^$\n]+?\$|\\\([^)]+?\\\)/g, (match) => {
      const placeholder = `___MATH_PROTECTED_${mathIndex}___`;
      mathProtected[mathIndex++] = match;
      return placeholder;
    });
    
    // 现在可以安全地处理转义字符
    result = result.replace(/\\_(?![^<]*>)/g, '_');
    result = result.replace(/\\&/g, '&');
    result = result.replace(/\\%/g, '%');
    result = result.replace(/\\#/g, '#');
    // 不处理 \$ 因为它可能在数学上下文中使用
    // result = result.replace(/\\\$/g, '$');
    // 不处理 \{ \} 因为它们在数学模式中有特殊含义
    // result = result.replace(/\\{/g, '{');
    // result = result.replace(/\\}/g, '}');
    
    // 恢复数学模式内容
    for (let i = 0; i < mathProtected.length; i++) {
      result = result.replace(`___MATH_PROTECTED_${i}___`, mathProtected[i]);
    }
    
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
