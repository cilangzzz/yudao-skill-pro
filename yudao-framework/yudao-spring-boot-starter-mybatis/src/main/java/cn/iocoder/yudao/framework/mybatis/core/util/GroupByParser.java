package cn.iocoder.yudao.framework.mybatis.core.util;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * GROUP BY 子句解析器
 * <p>
 * 用于解析 SQL 片段中的 GROUP BY 子句，支持：
 * 1. 普通字段：t.id, post_time
 * 2. 函数表达式：DATE(create_time), YEAR(post_time)
 * 3. CASE 表达式：CASE WHEN t.status = 1 THEN 'A' ELSE 'B' END
 * <p>
 * 使用场景：
 * 两阶段查询优化时，需要从 GROUP BY 子句提取分组字段，
 * 用于聚合查询或统计查询。
 * <p>
 * 使用示例：
 * <pre>
 * // 获取分组字段的 SQL 字符串
 * String groupFields = GroupByParser.getGroupByColumnSql(
 *     "WHERE status = 1 GROUP BY t.dept_id, DATE(create_time)"
 * );
 * // 结果: "t.dept_id, DATE(create_time)"
 *
 * // 解析分组字段列表
 * List&lt;String&gt; fields = GroupByParser.parseGroupBy(
 *     "GROUP BY CASE WHEN type=1 THEN 'A' ELSE 'B' END, name"
 * );
 * // 结果: ["CASE WHEN type=1 THEN 'A' ELSE 'B' END", "name"]
 * </pre>
 *
 * @author yudao-framework
 * @see SqlField
 * @see SqlSegmentParser
 */
public class GroupByParser {

    /**
     * GROUP BY 子句的正则表达式
     * 匹配 GROUP BY 之后的内容，直到遇到 HAVING, ORDER BY, LIMIT 或字符串末尾
     */
    private static final Pattern GROUP_BY_PATTERN = Pattern.compile(
            "GROUP\\s+BY\\s+(.+?)(?:\\s+(?:HAVING|ORDER\\s+BY|LIMIT|OFFSET|FOR|$))?$",
            Pattern.CASE_INSENSITIVE
    );

    private GroupByParser() {
        // 工具类，禁止实例化
    }

    // ==================== 核心方法 ====================

    /**
     * 获取 GROUP BY 字段的 SQL 字符串
     * <p>
     * 用于提取分组字段，可用于 SELECT 子句。
     *
     * @param sqlSegment SQL 片段（包含 GROUP BY 子句）
     * @return 分组字段的 SQL 字符串，多个字段用逗号分隔
     */
    public static String getGroupByColumnSql(String sqlSegment) {
        List<String> groupFields = parseGroupBy(sqlSegment);
        return String.join(", ", groupFields);
    }

    /**
     * 从 SQL 片段解析分组字段列表
     *
     * @param sqlSegment SQL 片段（可能包含 GROUP BY 子句）
     * @return 分组字段列表
     */
    public static List<String> parseGroupBy(String sqlSegment) {
        List<String> result = new ArrayList<>();

        if (sqlSegment == null) {
            return result;
        }

        // 提取 GROUP BY 子句
        Matcher matcher = GROUP_BY_PATTERN.matcher(sqlSegment);
        if (!matcher.find()) {
            return result;
        }

        String groupClause = matcher.group(1);
        return parseGroupClause(groupClause);
    }

    /**
     * 解析 GROUP BY 子句内容
     * <p>
     * 使用 SqlSegmentParser.splitByComma 正确处理：
     * - 函数表达式中的括号嵌套
     * - CASE 表达式中的逗号
     *
     * @param groupClause GROUP BY 后面的内容
     * @return 分组字段列表
     */
    public static List<String> parseGroupClause(String groupClause) {
        if (groupClause == null || groupClause.trim().isEmpty()) {
            return new ArrayList<>();
        }

        // 使用通用工具分割字段（支持函数表达式和 CASE 表达式）
        return SqlSegmentParser.splitByComma(groupClause);
    }

    /**
     * 从 SQL 片段解析分组字段，返回 SqlField 列表
     * <p>
     * GROUP BY 没有 ASC/DESC 概念，所以 SqlField 的 direction 为 null
     *
     * @param sqlSegment SQL 片段
     * @return 分组字段列表（SqlField 格式，direction 为 null）
     */
    public static List<SqlField> parseGroupByAsFields(String sqlSegment) {
        List<String> fields = parseGroupBy(sqlSegment);
        return fields.stream()
                .map(SqlField::of)
                .collect(Collectors.toList());
    }

    // ==================== 工具方法 ====================

    /**
     * 构建 GROUP BY 子句
     *
     * @param fields 分组字段列表
     * @return GROUP BY 子句字符串
     */
    public static String buildGroupByClause(List<String> fields) {
        if (fields == null || fields.isEmpty()) {
            return "";
        }
        return String.join(", ", fields);
    }

    /**
     * 构建 GROUP BY 子句（使用 SqlField 列表）
     *
     * @param fields 分组字段列表
     * @return GROUP BY 子句字符串
     */
    public static String buildGroupByClauseFromFields(List<SqlField> fields) {
        if (fields == null || fields.isEmpty()) {
            return "";
        }
        return fields.stream()
                .map(SqlField::getField)
                .collect(Collectors.joining(", "));
    }

    /**
     * 判断 SQL 片段是否包含 GROUP BY 子句
     *
     * @param sqlSegment SQL 片段
     * @return 是否包含 GROUP BY
     */
    public static boolean hasGroupBy(String sqlSegment) {
        return SqlSegmentParser.containsGroupBy(sqlSegment);
    }

    /**
     * 从完整的 SQL 中移除 GROUP BY 子句
     * <p>
     * 用于某些需要去掉分组的场景
     *
     * @param sql 完整的 SQL
     * @return 移除 GROUP BY 后的 SQL
     */
    public static String removeGroupBy(String sql) {
        if (sql == null) {
            return null;
        }
        return sql.replaceAll("(?i)GROUP\\s+BY\\s+[^HAVING|ORDER|LIMIT|$]+", "").trim();
    }
}