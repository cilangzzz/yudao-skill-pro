package cn.iocoder.yudao.framework.mybatis.core.util;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * ORDER BY 子句解析器
 * <p>
 * 用于解析 SQL 片段中的 ORDER BY 子句，支持：
 * 1. 普通字段：t.id, post_time
 * 2. 函数表达式：FIELD(t.status, 1, 2, 3)
 * 3. CASE 表达式：CASE WHEN t.status = 1 THEN 0 ELSE 1 END
 * <p>
 * 使用场景：
 * 两阶段查询优化时，需要从 ORDER BY 子句提取排序字段用于 SELECT，
 * 以避免分页查询时排序失效。
 * <p>
 * 使用示例：
 * <pre>
 * // 获取排序字段的 SELECT SQL
 * String orderFields = OrderByParser.getOrderByColumnSql(
 *     "WHERE status = 1 ORDER BY t.id DESC, post_time ASC",
 *     "t.id"
 * );
 * // 结果: "t.id, post_time"
 *
 * // 解析排序字段列表
 * List&lt;SqlField&gt; fields = OrderByParser.parseOrderBy(
 *     "ORDER BY FIELD(t.status, 1, 2) DESC, create_time ASC"
 * );
 * // 结果: [SqlField("FIELD(t.status, 1, 2)", "DESC"), SqlField("create_time", "ASC")]
 * </pre>
 *
 * @author yudao-framework
 * @see SqlField
 * @see SqlSegmentParser
 */
public class OrderByParser {

    /**
     * ORDER BY 子句的正则表达式
     * 匹配 ORDER BY 之后的内容，直到遇到 LIMIT, OFFSET, FOR, WHERE, GROUP BY, HAVING 或字符串末尾
     */
    private static final Pattern ORDER_BY_PATTERN = Pattern.compile(
            "ORDER\\s+BY\\s+(.+?)(?:\\s+(?:LIMIT|OFFSET|FOR|WHERE|GROUP\\s+BY|HAVING|$))?$",
            Pattern.CASE_INSENSITIVE
    );

    private OrderByParser() {
        // 工具类，禁止实例化
    }

    // ==================== 核心方法 ====================

    /**
     * 获取 ORDER BY 字段的 SELECT SQL 字符串
     * <p>
     * 用于两阶段查询优化，提取排序字段用于第一阶段 SELECT。
     *
     * @param sqlSegment   SQL 片段（包含 ORDER BY 子句）
     * @param defaultField 默认字段（当没有 ORDER BY 或解析失败时使用）
     * @return 排序字段的 SELECT SQL
     */
    public static String getOrderByColumnSql(String sqlSegment, String defaultField) {
        List<SqlField> orderFields = parseOrderBy(sqlSegment);

        if (orderFields.isEmpty()) {
            return defaultField;
        }

        // 提取所有字段名（包括函数表达式）
        String orderSql = orderFields.stream()
                .map(SqlField::getField)
                .collect(Collectors.joining(", "));

        if (orderSql.isEmpty()) {
            return defaultField;
        }

        // 确保默认字段包含在结果中
        return orderSql.contains(defaultField) ? orderSql : defaultField + ", " + orderSql;
    }

    /**
     * 从 SQL 片段解析排序字段列表
     *
     * @param sqlSegment SQL 片段（可能包含 ORDER BY 子句）
     * @return 排序字段列表
     */
    public static List<SqlField> parseOrderBy(String sqlSegment) {
        List<SqlField> result = new ArrayList<>();

        if (sqlSegment == null) {
            return result;
        }

        // 提取 ORDER BY 子句
        Matcher matcher = ORDER_BY_PATTERN.matcher(sqlSegment);
        if (!matcher.find()) {
            return result;
        }

        String orderClause = matcher.group(1);
        return parseOrderClause(orderClause);
    }

    /**
     * 解析 ORDER BY 子句内容
     *
     * @param orderClause ORDER BY 后面的内容
     * @return 排序字段列表
     */
    public static List<SqlField> parseOrderClause(String orderClause) {
        List<SqlField> result = new ArrayList<>();

        if (orderClause == null || orderClause.trim().isEmpty()) {
            return result;
        }

        // 使用通用工具分割字段
        List<String> fieldParts = SqlSegmentParser.splitByComma(orderClause);

        for (String field : fieldParts) {
            field = field.trim();
            if (field.isEmpty()) {
                continue;
            }

            SqlField sqlField = parseSingleField(field);
            if (sqlField != null) {
                result.add(sqlField);
            }
        }

        return result;
    }

    // ==================== 单字段解析 ====================

    /**
     * 解析单个排序字段
     *
     * @param field 字段字符串（可能包含 ASC/DESC）
     * @return SqlField 对象
     */
    private static SqlField parseSingleField(String field) {
        String upperField = field.toUpperCase();

        // 1. 处理 CASE 表达式
        if (upperField.startsWith("CASE")) {
            return parseCaseExpression(field);
        }

        // 2. 处理函数表达式
        if (SqlSegmentParser.isFunctionExpression(field)) {
            return parseFunctionExpression(field);
        }

        // 3. 处理普通字段
        return parseSimpleField(field);
    }

    /**
     * 解析 CASE 表达式
     */
    private static SqlField parseCaseExpression(String field) {
        int endIdx = SqlSegmentParser.findCaseEnd(field, 0);
        if (endIdx != -1) {
            String caseExpr = field.substring(0, endIdx + 3); // 包含 END
            String remaining = field.substring(endIdx + 3).trim();
            String direction = parseDirection(remaining);
            return new SqlField(caseExpr, direction);
        }
        // 没有 END，异常情况
        return new SqlField(field, SqlField.ASC);
    }

    /**
     * 解析函数表达式
     */
    private static SqlField parseFunctionExpression(String field) {
        int closeParenIdx = SqlSegmentParser.findMatchingCloseParen(field, field.indexOf('('));
        if (closeParenIdx != -1) {
            String funcExpr = field.substring(0, closeParenIdx + 1);
            String remaining = field.substring(closeParenIdx + 1).trim();
            String direction = parseDirection(remaining);
            return new SqlField(funcExpr, direction);
        }
        // 没有匹配的右括号
        return new SqlField(field, SqlField.ASC);
    }

    /**
     * 解析普通字段
     */
    private static SqlField parseSimpleField(String field) {
        String[] parts = field.split("\\s+");
        String fieldName = parts[0];
        String direction = parts.length > 1 ? parseDirection(parts[1]) : SqlField.ASC;
        return new SqlField(fieldName, direction);
    }

    /**
     * 解析排序方向
     */
    private static String parseDirection(String str) {
        if (str == null || str.isEmpty()) {
            return SqlField.ASC;
        }
        String upper = str.toUpperCase().trim();
        return upper.startsWith("DESC") ? SqlField.DESC : SqlField.ASC;
    }

    // ==================== 工具方法 ====================

    /**
     * 构建 ORDER BY 子句
     *
     * @param fields 排序字段列表
     * @return ORDER BY 子句字符串
     */
    public static String buildOrderByClause(List<SqlField> fields) {
        if (fields == null || fields.isEmpty()) {
            return "";
        }
        return fields.stream()
                .map(SqlField::toString)
                .collect(Collectors.joining(", "));
    }

    /**
     * 判断 SQL 片段是否包含 ORDER BY 子句
     *
     * @param sqlSegment SQL 片段
     * @return 是否包含 ORDER BY
     */
    public static boolean hasOrderBy(String sqlSegment) {
        return SqlSegmentParser.containsOrderBy(sqlSegment);
    }
}