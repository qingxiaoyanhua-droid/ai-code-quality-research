import re
import sys
from typing import Dict, List

def normalize_code(code: str) -> str:
    """去除注释、空白、换行，便于正则匹配"""
    # 去掉 // 注释
    code = re.sub(r'//.*', '', code)
    # 去掉 /* ... */ 注释
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)
    # 统一空白
    code = re.sub(r'\s+', ' ', code)
    return code

def evaluate_cpp_quicksort(code: str) -> None:
    code_norm = normalize_code(code)  # 归一化后的代码，用于正则匹配
    lines = code.splitlines()         # 原始代码，用于统计注释行数

    score = 0
    max_score = 100
    results = []

    def add(item: str, check: bool, points: int, note: str = ""):
        nonlocal score
        results.append({
            "项目": item,
            "结果": "✓" if check else "✗",
            "得分": points if check else 0,
            "满分": points,
            "说明": note or ("满足" if check else "不满足")
        })
        if check:
            score += points

    # 1. 模板实现
    add("1. 模板实现（泛型支持）", bool(re.search(r'template\s*<', code)), 8,
        "检测到 template<typename T> 或 template<class T>")

    # 2. Hoare分区（双指针特征）
    has_i_j = bool(re.search(r'int\s+i\s*=\s*low', code)) and bool(re.search(r'int\s+j\s*=\s*high', code))
    has_while_ij = "while(i<j)" in code_norm or "while(i < j)" in code_norm
    has_j_dec = "j--" in code_norm
    has_i_inc = "i++" in code_norm
    add("2. 使用Hoare双向指针分区", has_i_j and has_while_ij and has_j_dec and has_i_inc, 9,
        "必须同时有 i=low, j=high, while(i<j), i++, j--")

    # 3. 正确的Hoare条件（关键！很多AI实现这里写反）
    right_find_smaller = bool(re.search(r'arr\[j\][^=]*>=', code)) or bool(re.search(r'arr\[j\][^<]*<[^=]', code))  # arr[j] >= pivot 或 arr[j] < pivot
    left_find_larger  = bool(re.search(r'arr\[i\][^=]*<=', code)) or bool(re.search(r'arr\[i\][^>]*>[^=]', code))   # arr[i] <= pivot 或 arr[i] > pivot
    correct_hoare_condition = right_find_smaller and left_find_larger
    add("   ├ 正确的Hoare比较条件（防bug）", correct_hoare_condition, 8,
        "右找 >= 或 <，左找 <= 或 >（你原来的代码是 > 和 <=，会出大bug！）")

    # 4. 多种数据类型测试
    has_int    = "vector<int>" in code or 'vector < int >' in code_norm
    has_float  = "vector<float>" in code or 'vector < float >' in code_norm
    has_double = "vector<double>" in code or 'vector < double >' in code_norm
    multi_type = sum([has_int, has_float, has_double])
    add("3. 覆盖多种数值类型测试", multi_type >= 3, 7,
        f"检测到 int:{has_int} float:{has_float} double:{has_double}")

    # 5. 边界条件
    has_low_ge_high = "low >= high" in code_norm
    has_empty_check = "arr.empty()" in code_norm or "arr.size() == 0" in code_norm
    has_empty_test  = "emptyArr" in code or "vector<int>{}" in code
    boundary_ok = has_low_ge_high and (has_empty_check or has_empty_test)
    add("4. 边界条件处理完善", boundary_ok, 8, "空数组、单元素、low>=high 都要处理")

    # 6. 注释数量与质量
    comment_lines = sum(1 for line in lines if line.strip().startswith('//') or '/*' in line or '*/' in line)
    add("5. 中文注释详细", comment_lines >= 10, 8,
        f"检测到约 {comment_lines} 行注释")

    # 7. 代码结构良好（包装函数 + 打印函数）
    has_wrapper = bool(re.search(r'void\s+quickSort\s*\([^,]*vector', code)) and "0, arr.size()" in code
    has_print   = "printArray" in code or 'cout <<' in code
    add("6. 代码结构清晰（有包装/打印函数）", has_wrapper and has_print, 8, "可读性强")

    # 8. 命名规范
    bad_names = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
    bad = any(len(name) <= 2 and name not in {'i', 'j', 'T'} for name in bad_names)
    add("7. 命名规范", not bad, 6, "避免单字母变量（除i/j/low/high外）")

    # 9. 重复元素处理好（依赖上面正确的Hoare条件）
    add("8. 重复元素处理优秀", correct_hoare_condition, 7, "错误条件会导致重复值时分区极不平衡")

    # 10. 使用std::swap
    add("9. 使用高效std::swap", "swap(" in code or "std::swap" in code, 6, "")

    # 11. 递归调用正确
    has_rec_left  = re.search(r'quickSort\([^,]*,\s*[^,]*j\s*-\s*1', code)
    has_rec_right = re.search(r'quickSort\([^,]*,\s*[^,]*j\s*\+\s*1', code) or re.search(r'quickSort\([^,]*,\s*i\s*\+\s*1', code)
    add("10. 递归分区正确", bool(has_rec_left and has_rec_right), 8, "")

    # 12. 基准值放对位置（经典bug点）
    final_swap_j = "swap(arr[low], arr[j]" in code_norm
    final_swap_i = "swap(arr[low], arr[i]" in code_norm
    correct_final_swap = final_swap_i or (final_swap_j and not correct_hoare_condition)
    add("11. 基准值最终放置正确", correct_final_swap, 9,
        "标准Hoare循环结束时 i==j，应swap(low, i)。很多AI写swap(low, j)但条件又是对的，会错位！")

    # 输出报告
    print("=" * 80)
    print("      C++ 快速排序代码 智能测评报告（2025版）")
    print("=" * 80)
    print(f"{'项目':<40} {'结果':<6} {'得分':<6} {'说明'}")
    print("-" * 80)
    for r in results:
        print(f"{r['项目']:<40} {r['结果']:<6} {r['得分']}/{r['满分']:<6} {r['说明']}")
    print("-" * 80)
    print(f"{'总分':<40} {score}/{max_score}")
    print("\n评级：")
    if score >= 95:
        print("神作级（99+）     → 恭喜！可以直接进LeetCode官方题解")
    elif score >= 90:
        print("优秀（90-98）     → 生产可用，面试随便甩")
    elif score >= 80:
        print("良好（80-89）     → 核心正确，小优化即可完美")
    elif score >= 70:
        print("及格（70-79）     → 能跑，但有明显bug或坏味道")
    else:
        print("危险（<70）       → 存在严重逻辑错误，勿用于生产")

    return score

# ====================== 使用示例 ======================
if __name__ == "__main__":
    # 你原来通义千问生成的代码（有经典Hoare bug）
    bug_code = open("buggy_quicksort.cpp", "r", encoding="utf-8").read() if False else generated_code

    # 我修正后的完美版本（可另存为 correct_quicksort.cpp 测试对比）
    correct_code = """
    // 正确版本示例片段
    while (i < j) {
        while (i < j && arr[j] >= pivot) j--;
        while (i < j && arr[i] <= pivot) i++;
        if (i < j) swap(arr[i], arr[j]);
    }
    swap(arr[low], arr[i]);  // 注意这里是 i，不是 j！
    """

    print("正在测评你提供的代码……\n")
    final_score = evaluate_cpp_quicksort(generated_code)

    print("\n\n建议：")
    if final_score < 90:
        print("你的代码大概率中了AI最常见的Hoare分区bug！")
        print("请将两个while条件改为：")
        print("    while (i < j && arr[j] >= pivot) j--;")
        print("    while (i < j && arr[i] <= pivot) i++;")
        print("    并且最后 swap(arr[low], arr[i]);  // 用i而不是j")
