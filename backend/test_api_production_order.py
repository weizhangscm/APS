"""
测试API端点：验证通过API创建生产订单的默认状态

运行前需要确保后端服务已启动
"""

import requests
from datetime import datetime, timedelta
import json


BASE_URL = "http://localhost:8000/api"


def test_create_production_order_via_api():
    """测试通过API创建生产订单"""
    
    print("=" * 80)
    print("测试通过API创建生产订单")
    print("=" * 80)
    
    try:
        # 1. 获取第一个产品
        print("\n1. 获取产品列表...")
        response = requests.get(f"{BASE_URL}/products")
        if response.status_code != 200:
            print(f"错误: 无法获取产品列表 (状态码: {response.status_code})")
            return
        
        products = response.json()
        if not products:
            print("错误: 没有可用的产品")
            return
        
        product = products[0]
        print(f"使用产品: {product['name']} (ID: {product['id']})")
        
        # 2. 创建生产订单
        print("\n2. 创建生产订单...")
        
        test_order_number = f"TEST_API_PRD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order_data = {
            "order_number": test_order_number,
            "order_type": "production",  # 生产订单
            "product_id": product['id'],
            "quantity": 10,
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": 3,
            "status": "created",  # 即使传入created，API应该覆盖为scheduled
            "confirmed_start": (datetime.now() + timedelta(days=1)).isoformat(),
            "confirmed_end": (datetime.now() + timedelta(days=3)).isoformat(),
            "description": "测试生产订单 - API创建"
        }
        
        response = requests.post(f"{BASE_URL}/orders/", json=order_data)
        
        if response.status_code != 200:
            print(f"错误: 创建订单失败 (状态码: {response.status_code})")
            print(f"响应: {response.text}")
            return
        
        created_order = response.json()
        order_id = created_order['id']
        
        print(f"\n创建成功!")
        print(f"订单号: {created_order['order_number']}")
        print(f"订单类型: {created_order['order_type']}")
        print(f"订单状态: {created_order['status']}")
        
        # 3. 检查工序状态
        print(f"\n3. 检查工序状态...")
        
        operations = created_order.get('operations', [])
        print(f"工序数量: {len(operations)}")
        
        if operations:
            print("\n工序详情:")
            for op in operations:
                print(f"  工序 {op['sequence']:02d} - {op['name']}: 状态={op['status']}")
            
            # 统计工序状态
            status_counts = {}
            for op in operations:
                status = op['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n工序状态分布: {status_counts}")
        
        # 4. 验证结果
        print("\n" + "=" * 80)
        print("验证结果")
        print("=" * 80)
        
        success = True
        
        # 检查订单状态
        if created_order['status'] == 'scheduled':
            print("[成功] 订单状态为 'scheduled' ✓")
        else:
            print(f"[失败] 订单状态为 '{created_order['status']}'，期望 'scheduled' ✗")
            success = False
        
        # 检查工序状态
        if operations:
            all_scheduled = all(op['status'] == 'scheduled' for op in operations)
            if all_scheduled:
                print("[成功] 所有工序状态为 'scheduled' ✓")
            else:
                non_scheduled = [op for op in operations if op['status'] != 'scheduled']
                print(f"[失败] 有 {len(non_scheduled)} 个工序状态不是 'scheduled' ✗")
                success = False
        
        # 5. 清理测试数据
        print(f"\n5. 清理测试数据...")
        response = requests.delete(f"{BASE_URL}/orders/{order_id}")
        if response.status_code == 200:
            print(f"[完成] 测试订单已删除")
        else:
            print(f"[警告] 删除订单失败 (状态码: {response.status_code})")
        
        # 总结
        print("\n" + "=" * 80)
        if success:
            print("测试通过! 生产订单及其工序的默认状态已正确设置为 'scheduled'")
        else:
            print("测试失败! 请检查API端点代码")
        print("=" * 80)
        
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到后端服务")
        print("请确保后端服务已启动 (运行 uvicorn main:app --reload)")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


def test_convert_to_production_via_api():
    """测试通过API将计划订单转换为生产订单"""
    
    print("\n\n" + "=" * 80)
    print("测试将计划订单转换为生产订单")
    print("=" * 80)
    
    try:
        # 获取一个已排程的计划订单
        print("\n1. 查找已排程的计划订单...")
        response = requests.get(f"{BASE_URL}/orders/?order_type=planned&status=scheduled")
        
        if response.status_code != 200:
            print(f"错误: 无法获取订单列表 (状态码: {response.status_code})")
            return
        
        orders = response.json()
        scheduled_orders = [o for o in orders if o['status'] == 'scheduled']
        
        if not scheduled_orders:
            print("没有找到已排程的计划订单，跳过此测试")
            return
        
        test_order = scheduled_orders[0]
        print(f"找到计划订单: {test_order['order_number']} (ID: {test_order['id']})")
        print(f"当前状态: {test_order['status']}")
        
        # 转换为生产订单
        print(f"\n2. 转换为生产订单...")
        response = requests.post(f"{BASE_URL}/orders/{test_order['id']}/convert-to-production")
        
        if response.status_code != 200:
            print(f"错误: 转换失败 (状态码: {response.status_code})")
            print(f"响应: {response.text}")
            return
        
        converted_order = response.json()
        
        print(f"\n转换成功!")
        print(f"订单类型: {converted_order['order_type']}")
        print(f"订单状态: {converted_order['status']}")
        
        # 获取完整订单信息（包含工序）
        print(f"\n3. 获取转换后的订单详情...")
        response = requests.get(f"{BASE_URL}/orders/{test_order['id']}")
        
        if response.status_code != 200:
            print(f"错误: 无法获取订单详情")
            return
        
        order_details = response.json()
        operations = order_details.get('operations', [])
        
        print(f"工序数量: {len(operations)}")
        
        if operations:
            # 统计工序状态
            status_counts = {}
            for op in operations:
                status = op['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"工序状态分布: {status_counts}")
        
        # 验证结果
        print("\n" + "=" * 80)
        print("验证结果")
        print("=" * 80)
        
        success = True
        
        if converted_order['order_type'] == 'production':
            print("[成功] 订单类型为 'production' ✓")
        else:
            print(f"[失败] 订单类型为 '{converted_order['order_type']}' ✗")
            success = False
        
        if converted_order['status'] == 'scheduled':
            print("[成功] 订单状态为 'scheduled' ✓")
        else:
            print(f"[失败] 订单状态为 '{converted_order['status']}' ✗")
            success = False
        
        if operations:
            all_scheduled = all(op['status'] == 'scheduled' for op in operations)
            if all_scheduled:
                print("[成功] 所有工序状态为 'scheduled' ✓")
            else:
                non_scheduled = [op for op in operations if op['status'] != 'scheduled']
                print(f"[失败] 有 {len(non_scheduled)} 个工序状态不是 'scheduled' ✗")
                success = False
        
        print("\n" + "=" * 80)
        if success:
            print("测试通过! 转换后的生产订单状态正确")
        else:
            print("测试失败! 请检查转换端点代码")
        print("=" * 80)
        
        print(f"\n注意: 已将订单 {test_order['order_number']} 转换为生产订单，未删除")
        
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到后端服务")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_create_production_order_via_api()
    test_convert_to_production_via_api()
