#!/usr/bin/env python3
"""
查询链上 USDC 余额的脚本

使用方法：
    python check_balances.py

功能：
    - 查询所有 5 个员工的 USDC 余额
    - 查询 PayrollVault 的 USDC 余额
    - 自动转换为可读格式
"""

from web3 import Web3
import os

# ========================================
# 配置
# ========================================

# 连接到 Hardhat 本地节点
# 在 Docker 容器内运行时，使用 host.docker.internal 访问宿主机
# 在容器外运行时，使用 localhost
import platform
import socket

def get_rpc_url():
    """
    自动检测 RPC URL
    
    如果在 Docker 容器内运行，使用 host.docker.internal
    否则使用 localhost
    """
    try:
        # 尝试解析 host.docker.internal（Docker Desktop 提供）
        socket.gethostbyname('host.docker.internal')
        return "http://host.docker.internal:8545"
    except socket.gaierror:
        # 不在 Docker 内或不支持 host.docker.internal
        return "http://127.0.0.1:8545"

RPC_URL = get_rpc_url()
print(f"🔗 尝试连接到：{RPC_URL}")

web3 = Web3(Web3.HTTPProvider(RPC_URL))

# 检查连接
if not web3.is_connected():
    print("❌ 无法连接到 Hardhat 节点")
    print(f"   请确保 Hardhat 节点正在运行：{RPC_URL}")
    exit(1)

print("✅ 已连接到 Hardhat 节点")
print()

# 合约地址（从环境变量或硬编码）
# 替换成你的实际地址！
USDC_ADDRESS = os.getenv("USDC_ADDRESS", "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512")
PAYROLL_CONTRACT_ADDRESS = os.getenv("PAYROLL_CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")

# 员工钱包地址（来自 node_ingest.py 的假数据）
EMPLOYEES = [
    {"name": "Alice Smith", "id": "emp_001", "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"},
    {"name": "Bob Johnson", "id": "emp_002", "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"},
    {"name": "Carol Williams", "id": "emp_003", "address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906"},
    {"name": "David Brown", "id": "emp_004", "address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"},
    {"name": "Eve Davis", "id": "emp_005", "address": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"},
]

# ERC20 balanceOf 函数的 ABI
BALANCE_OF_ABI = {
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function"
}

# ========================================
# 主要功能
# ========================================

def get_balance(token_address: str, wallet_address: str) -> int:
    """
    查询指定钱包的代币余额
    
    Args:
        token_address: 代币合约地址
        wallet_address: 要查询的钱包地址
        
    Returns:
        余额（最小单位）
    """
    # 创建合约实例
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(token_address),
        abi=[BALANCE_OF_ABI]
    )
    
    # 调用 balanceOf 函数
    balance = contract.functions.balanceOf(
        Web3.to_checksum_address(wallet_address)
    ).call()
    
    return balance


def format_usdc(amount: int) -> str:
    """
    将 USDC 最小单位转换为可读格式
    
    USDC 使用 6 位小数
    例如：5500000000 -> "5,500.00 USDC"
    
    Args:
        amount: USDC 数量（最小单位）
        
    Returns:
        格式化的字符串
    """
    # 除以 10^6 转换为 USDC
    usdc_amount = amount / 1_000_000
    
    # 格式化为千位分隔符
    return f"{usdc_amount:,.2f} USDC"


# ========================================
# 主程序
# ========================================

def main():
    print("=" * 60)
    print("💰 USDC 余额查询")
    print("=" * 60)
    print()
    
    # 查询员工余额
    print("👥 员工余额：")
    print("-" * 60)
    
    total = 0
    for emp in EMPLOYEES:
        try:
            balance = get_balance(USDC_ADDRESS, emp["address"])
            formatted = format_usdc(balance)
            total += balance
            
            print(f"  {emp['name']:20} ({emp['id']}): {formatted:>15}")
        except Exception as e:
            print(f"  {emp['name']:20} ({emp['id']}): ❌ 错误: {e}")
    
    print("-" * 60)
    print(f"  {'总计':20}             {format_usdc(total):>15}")
    print()
    
    # 查询 PayrollVault 余额
    print("🏦 PayrollVault 余额：")
    print("-" * 60)
    
    try:
        vault_balance = get_balance(USDC_ADDRESS, PAYROLL_CONTRACT_ADDRESS)
        formatted = format_usdc(vault_balance)
        print(f"  PayrollVault: {formatted}")
        print()
        print(f"  说明：")
        print(f"    - 初始充值：100,000 USDC")
        print(f"    - 已发放：{format_usdc(total)}")
        print(f"    - 剩余：{formatted}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    print()
    print("=" * 60)
    print("✅ 查询完成")
    print("=" * 60)


if __name__ == "__main__":
    main()

