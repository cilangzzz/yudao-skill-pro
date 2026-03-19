package cn.iocoder.yudao.framework.mybatis.core.util;

import java.io.Serializable;

/**
 * SQL 字段信息
 * <p>
 * 可用于 ORDER BY、GROUP BY 等 SQL 子句的字段表示。
 * 支持：
 * 1. 普通字段：t.id, post_time
 * 2. 函数表达式：FIELD(...), MAX(...)
 * 3. CASE 表达式：CASE WHEN ... END
 * <p>
 * 使用示例：
 * <pre>
 * // ORDER BY 字段
 * SqlField orderField = new SqlField("t.id", "DESC");
 * SqlField caseField = new SqlField("CASE t.status WHEN 1 THEN 0 ELSE 1 END", "ASC");
 *
 * // GROUP BY 字段（无排序方向）
 * SqlField groupField = new SqlField("DATE(create_time)");
 * </pre>
 *
 * @author yudao-framework
 */
public class SqlField implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 升序排序
     */
    public static final String ASC = "ASC";

    /**
     * 降序排序
     */
    public static final String DESC = "DESC";

    /**
     * 字段名或表达式
     * <p>
     * 示例：
     * - "t.id"
     * - "post_time"
     * - "FIELD(t.status, 1, 2, 3)"
     * - "CASE WHEN t.status = 1 THEN 0 ELSE 1 END"
     */
    private String field;

    /**
     * 排序方向 (ASC/DESC)
     * <p>
     * 仅 ORDER BY 使用，GROUP BY 时为 null
     */
    private String direction;

    // ==================== 构造方法 ====================

    public SqlField() {
    }

    /**
     * 构造字段信息（无排序方向，适用于 GROUP BY）
     *
     * @param field 字段名或表达式
     */
    public SqlField(String field) {
        this.field = field;
    }

    /**
     * 构造字段信息（带排序方向，适用于 ORDER BY）
     *
     * @param field     字段名或表达式
     * @param direction 排序方向 (ASC/DESC)
     */
    public SqlField(String field, String direction) {
        this.field = field;
        this.direction = direction;
    }

    // ==================== 静态工厂方法 ====================

    /**
     * 创建升序字段
     */
    public static SqlField asc(String field) {
        return new SqlField(field, ASC);
    }

    /**
     * 创建降序字段
     */
    public static SqlField desc(String field) {
        return new SqlField(field, DESC);
    }

    /**
     * 创建分组字段（无排序方向）
     */
    public static SqlField of(String field) {
        return new SqlField(field);
    }

    // ==================== getter/setter ====================

    public String getField() {
        return field;
    }

    public void setField(String field) {
        this.field = field;
    }

    public String getDirection() {
        return direction;
    }

    public void setDirection(String direction) {
        this.direction = direction;
    }

    // ==================== 便捷方法 ====================

    /**
     * 是否为升序
     */
    public boolean isAsc() {
        return ASC.equalsIgnoreCase(direction);
    }

    /**
     * 是否为降序
     */
    public boolean isDesc() {
        return DESC.equalsIgnoreCase(direction);
    }

    /**
     * 是否有排序方向
     */
    public boolean hasDirection() {
        return direction != null && !direction.isEmpty();
    }

    // ==================== Object 方法 ====================

    @Override
    public String toString() {
        if (hasDirection()) {
            return field + " " + direction;
        }
        return field;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        SqlField sqlField = (SqlField) o;
        if (field != null ? !field.equals(sqlField.field) : sqlField.field != null) return false;
        return direction != null ? direction.equals(sqlField.direction) : sqlField.direction == null;
    }

    @Override
    public int hashCode() {
        int result = field != null ? field.hashCode() : 0;
        result = 31 * result + (direction != null ? direction.hashCode() : 0);
        return result;
    }
}