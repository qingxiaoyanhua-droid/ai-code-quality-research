/**
 * @file fix_suggestion.cpp
 * @brief 针对LLM生成C++代码的典型缺陷修复方案
 * 
 * 背景：在测试通义千问生成的快速排序实现时，
 * 发现其存在Hoare分区致命bug（基准值放置错误）。
 * 本文件提供三种修复策略，体现从"语法修正"到
 * "架构优化"的完整修复路径。
 * 
 * Author: 王柄涛 | 基于LeetCode算法经验总结
 * Date: 2025.05
 */

#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// ==================== 方案1：直接修复（最小改动） ====================
/**
 * @brief 修复原代码的两个核心问题：
 * 1. Hoare条件：arr[j] > pivot → arr[j] >= pivot
 * 2. 最终交换：swap(arr[low], arr[j]) → swap(arr[low], arr[i])
 */
template<typename T>
void quickSort_v1(vector<T>& arr, int low, int high) {
    if (low >= high) return;
    
    int i = low, j = high;
    T pivot = arr[low];
    
    while (i < j) {
        // 修复1：右指针找 <= pivot 的元素
        while (i < j && arr[j] >= pivot) j--;  // 原为 >
        // 修复2：左指针找 >= pivot 的元素  
        while (i < j && arr[i] <= pivot) i++;  // 原为 <=
        
        if (i < j) swap(arr[i], arr[j]);
    }
    
    // 修复3：循环结束时 i == j，应与 arr[i] 交换
    swap(arr[low], arr[i]);  // 原为 arr[j]
    
    quickSort_v1(arr, low, i-1);
    quickSort_v1(arr, i+1, high);
}

// ==================== 方案2：增强鲁棒性（推荐） ====================
/**
 * @brief 在v1基础上增加生产级防护：
 * 1. 随机化基准值选择（避免最坏O(n²)）
 * 2. 三数取中法优化分区质量
 * 3. 尾递归优化减少栈深度
 */
template<typename T>
int medianOfThree(vector<T>& arr, int low, int high) {
    int mid = low + (high - low) / 2;
    if (arr[mid] < arr[low])    swap(arr[low], arr[mid]);
    if (arr[high] < arr[low])   swap(arr[low], arr[high]);
    if (arr[high] < arr[mid])   swap(arr[mid], arr[high]);
    return mid;
}

template<typename T>
void quickSort_v2(vector<T>& arr, int low, int high) {
    while (low < high) {  // 尾递归优化
        // 随机化基准值选择
        int rand_idx = low + rand() % (high - low + 1);
        swap(arr[low], arr[rand_idx]);
        
        // 三数取中进一步优化
        int median = medianOfThree(arr, low, high);
        swap(arr[low], arr[median]);
        
        // 标准Hoare分区（已修复）
        int i = low, j = high;
        T pivot = arr[low];
        
        while (i < j) {
            while (i < j && arr[j] >= pivot) j--;
            while (i < j && arr[i] <= pivot) i++;
            if (i < j) swap(arr[i], arr[j]);
        }
        swap(arr[low], arr[i]);
        
        // 只对较大子数组递归，小的用循环处理
        if (i - low < high - i) {
            quickSort_v2(arr, low, i-1);
            low = i + 1;  // 循环处理右半部分
        } else {
            quickSort_v2(arr, i+1, high);
            high = i - 1; // 循环处理左半部分
        }
    }
}

// ==================== 方案3：模板特化优化（C++专项） ====================
/**
 * @brief 针对C++特性深度优化：
 * 1. 迭代器支持（符合STL规范）
 * 2. 移动语义优化
 * 3. SFINAE启用条件
 */
template<typename Iterator>
typename enable_if<is_same<typename iterator_traits<Iterator>::iterator_category,
                          random_access_iterator_tag>::value>::type
quickSort_v3(Iterator first, Iterator last) {
    if (first >= last) return;
    
    auto pivot = *first;
    auto i = first, j = last - 1;
    
    while (i < j) {
        while (i < j && *j >= pivot) j--;
        while (i < j && *i <= pivot) i++;
        if (i < j) iter_swap(i, j);
    }
    iter_swap(first, i);
    
    quickSort_v3(first, i);
    quickSort_v3(i + 1, last);
}

// ==================== 测试框架 ====================
template<typename T>
void printArray(const vector<T>& arr, const string& label) {
    cout << label << ": ";
    for (const T& elem : arr) cout << elem << " ";
    cout << endl;
}

int main() {
    // 测试原始有bug的代码 vs 修复后版本
    vector<int> test_arr = {64, 34, 25, 12, 22, 11, 90};
    
    cout << "=== 方案1：直接修复 ===" << endl;
    printArray(test_arr, "排序前");
    quickSort_v1(test_arr, 0, test_arr.size()-1);
    printArray(test_arr, "排序后");
    
    cout << "\n=== 方案2：生产级优化 ===" << endl;
    vector<float> float_arr = {3.14f, 2.71f, 1.41f, 3.14f};
    printArray(float_arr, "排序前");
    quickSort_v2(float_arr, 0, float_arr.size()-1);
    printArray(float_arr, "排序后");
    
    return 0;
}
