package cn.iocoder.yudao.framework.mybatis.core.util;

import java.util.ArrayList;
import java.util.List;

/**
 * SQL 片段解析通用工具
 * <p>
 * 提供字段分割、括号匹配等通用方法，用于解析 SQL 片段。
 * 支持：
 * 1. 按逗号分割字段列表，正确处理括号嵌套和 CASE 表达式
 * 2. 找到匹配的右括号位置
 * 3. 找到 CASE 表达式的 END 关键字位置
 * 4. 判断是否为函数表达式
 * <p>
 * 使用示例：
 * <pre>
 * // 分割字段列表
 * List&lt;String&gt; fields = SqlSegmentParser.splitByComma("t.id, CASE WHEN a=1 THEN 'A' END, name");
 * // 结果: ["t.id", "CASE WHEN a=1 THEN 'A' END", "name"]
 *
 * // 判断是否为函数表达式
 * boolean isFunc = SqlSegmentParser.isFunctionExpression("FIELD(t.status, 1, 2)");
 * // 结果: true
 * </pre>
 *
 * @author yudao-framework
 */
public final class SqlSegmentParser {

    private SqlSegmentParser() {
        // 工具类，禁止实例化
    }

    // ==================== 字段分割 ====================

    /**
     * 按逗号分割 SQL 字段列表，正确处理括号嵌套和 CASE 表达式
     * <p>
     * 示例：
     * <pre>
     * 输入: "t.id, MAX(score), CASE WHEN type=1 THEN 'A' ELSE 'B' END, name"
     * 输出: ["t.id", "MAX(score)", "CASE WHEN type=1 THEN 'A' ELSE 'B' END", "name"]
     * </pre>
     *
     * @param sql SQL 字段列表字符串
     * @return 分割后的字段列表
     */
    public static List<String> splitByComma(String sql) {
        List<String> result = new ArrayList<>();
        if (sql == null || sql.trim().isEmpty()) {
            return result;
        }

        StringBuilder current = new StringBuilder();
        int caseDepth = 0;
        int parenthesisDepth = 0;

        for (int i = 0; i < sql.length(); i++) {
            char c = sql.charAt(i);

            // 跟踪括号嵌套
            if (c == '(') {
                parenthesisDepth++;
            } else if (c == ')') {
                parenthesisDepth--;
            }

            // 检测 CASE 关键字开始
            if (isKeywordStart(sql, i, "CASE")) {
                caseDepth++;
            }

            // 检测 END 关键字结束
            if (caseDepth > 0 && isKeywordEnd(sql, i, "END")) {
                caseDepth--;
            }

            // 只有在不在 CASE 内部且不在括号内部时，逗号才作为字段分隔符
            if (c == ',' && caseDepth == 0 && parenthesisDepth == 0) {
                String field = current.toString().trim();
                if (!field.isEmpty()) {
                    result.add(field);
                }
                current = new StringBuilder();
            } else {
                current.append(c);
            }
        }

        // 添加最后一个字段
        String lastField = current.toString().trim();
        if (!lastField.isEmpty()) {
            result.add(lastField);
        }

        return result;
    }

    // ==================== 括号匹配 ====================

    /**
     * 找到与指定位置的左括号匹配的右括号
     *
     * @param str   字符串
     * @param start 开始位置（左括号位置）
     * @return 匹配的右括号位置，未找到返回 -1
     */
    public static int findMatchingCloseParen(String str, int start) {
        if (str == null || start < 0 || start >= str.length()) {
            return -1;
        }

        int parenDepth = 0;
        int caseDepth = 0;

        for (int i = start; i < str.length(); i++) {
            char c = str.charAt(i);

            // 跟踪 CASE...END 嵌套
            if (isKeywordStart(str, i, "CASE")) {
                caseDepth++;
            }
            if (caseDepth > 0 && isKeywordEnd(str, i, "END")) {
                caseDepth--;
            }

            if (c == '(') {
                parenDepth++;
            } else if (c == ')') {
                parenDepth--;
                if (parenDepth == 0) {
                    return i;
                }
            }
        }
        return -1;
    }

    // ==================== CASE 表达式解析 ====================

    /**
     * 找到 CASE 表达式的 END 关键字位置
     *
     * @param str   字符串
     * @param start 开始位置
     * @return END 关键字的起始位置，未找到返回 -1
     */
    public static int findCaseEnd(String str, int start) {
        if (str == null || start < 0) {
            return -1;
        }

        int caseDepth = 0;

        for (int i = start; i < str.length(); i++) {
            // 检测 CASE 关键字开始
            if (isKeywordStart(str, i, "CASE")) {
                caseDepth++;
            }

            // 检测 END 关键字结束
            if (caseDepth > 0 && isKeywordEnd(str, i, "END")) {
                caseDepth--;
                if (caseDepth == 0) {
                    return i;
                }
            }
        }
        return -1;
    }

    /**
     * 判断字符串指定位置是否是 CASE 表达式的开始
     *
     * @param str 字符串
     * @param pos 位置
     * @return 是否是 CASE 开始
     */
    public static boolean isCaseStart(String str, int pos) {
        return isKeywordStart(str, pos, "CASE");
    }

    // ==================== 函数表达式判断 ====================

    /**
     * 判断是否为函数表达式
     * <p>
     * 函数表达式：以函数名开头且紧跟左括号
     * <p>
     * 示例：
     * - "FIELD(t.status, 1, 2)" -> true
     * - "MAX(score)" -> true
     * - "t.id" -> false
     * - "(a + b)" -> false
     *
     * @param field 字段字符串
     * @return 是否为函数表达式
     */
    public static boolean isFunctionExpression(String field) {
        if (field == null || field.isEmpty()) {
            return false;
        }

        // 查找第一个左括号的位置
        int parenIdx = field.indexOf('(');
        if (parenIdx <= 0) {
            return false;
        }

        // 检查括号前是否是有效的函数名（字母开头，可包含字母、数字、下划线）
        String beforeParen = field.substring(0, parenIdx).trim();
        return beforeParen.matches("[A-Za-z_][A-Za-z0-9_]*");
    }

    // ==================== 辅助方法 ====================

    /**
     * 判断指定位置是否是某个关键字的开头（独立单词）
     *
     * @param str     字符串
     * @param pos     位置
     * @param keyword 关键字（如 "CASE", "END"）
     * @return 是否是关键字开头
     */
    private static boolean isKeywordStart(String str, int pos, String keyword) {
        int len = keyword.length();
        if (pos + len > str.length()) {
            return false;
        }

        // 检查是否匹配关键字（忽略大小写）
        if (!str.substring(pos, pos + len).equalsIgnoreCase(keyword)) {
            return false;
        }

        // 检查前面是否是单词边界（空格、括号、或字符串开头）
        if (pos > 0) {
            char prevChar = str.charAt(pos - 1);
            if (!Character.isWhitespace(prevChar) && prevChar != '(' && prevChar != ',') {
                return false;
            }
        }

        return true;
    }

    /**
     * 判断指定位置是否是某个关键字的结尾（独立单词）
     *
     * @param str     字符串
     * @param pos     位置
     * @param keyword 关键字（如 "END"）
     * @return 是否是关键字结尾
     */
    private static boolean isKeywordEnd(String str, int pos, String keyword) {
        int len = keyword.length();
        if (pos + len > str.length()) {
            return false;
        }

        // 检查是否匹配关键字（忽略大小写）
        if (!str.substring(pos, pos + len).equalsIgnoreCase(keyword)) {
            return false;
        }

        // 检查后面是否是单词边界（空格、括号、逗号、或字符串结尾）
        int endPos = pos + len;
        if (endPos < str.length()) {
            char nextChar = str.charAt(endPos);
            if (!Character.isWhitespace(nextChar) && nextChar != ')' && nextChar != ',') {
                return false;
            }
        }

        return true;
    }

    // ==================== SQL 关键字检测 ====================

    /**
     * 判断字符串是否以 ORDER BY 子句开头（不区分大小写）
     *
     * @param sql SQL 字符串
     * @return 是否包含 ORDER BY
     */
    public static boolean containsOrderBy(String sql) {
        if (sql == null) return false;
        return sql.toUpperCase().contains("ORDER BY");
    }

    /**
     * 判断字符串是否以 GROUP BY 子句开头（不区分大小写）
     *
     * @param sql SQL 字符串
     * @return 是否包含 GROUP BY
     */
    public static boolean containsGroupBy(String sql) {
        if (sql == null) return false;
        return sql.toUpperCase().contains("GROUP BY");
    }
}