// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {Pausable} from "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title IERC20
 * @dev ERC20 代幣介面，用於與 USDC 互動
 */
interface IERC20 {
    function decimals() external view returns (uint8);
    function transfer(address to, uint256 amount) external returns (bool);
}

/**
 * @title PayrollVault
 * @dev 薪資批次發放智慧合約
 * 
 * 功能說明：
 * - 支援批次發放 USDC 薪資
 * - 角色權限控制（APPROVER_ROLE 批准發放、OPERATOR_ROLE 操作）
 * - 可暫停/恢復功能
 * - 防重放攻擊（每個 batchId 只能處理一次）
 * - 完整事件記錄
 * 
 * 角色說明：
 * - DEFAULT_ADMIN_ROLE: 最高管理員，可設定限額、暫停合約、授予角色
 * - APPROVER_ROLE: 批准者，可執行批次發薪
 * - OPERATOR_ROLE: 操作者，保留給未來擴展使用
 */
contract PayrollVault is AccessControl, Pausable {
    // ============ 角色定義 ============
    // APPROVER_ROLE: 薪資批准者角色，允許執行 batchPayout
    bytes32 public constant APPROVER_ROLE = keccak256("APPROVER_ROLE");
    
    // OPERATOR_ROLE: 操作者角色，保留給未來功能擴展
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");

    // ============ 狀態變數 ============
    // USDC 代幣合約地址（不可變）
    address public immutable USDC;
    
    // 每月發薪上限（可由管理員調整）
    uint256 public monthlyCap;
    
    // 記錄已處理的批次 ID，防止重複發放
    mapping(bytes32 => bool) public processedBatch;

    // ============ 事件定義 ============
    /**
     * @dev 批次批准事件
     * @param batchId 批次唯一識別碼
     * @param approver 批准者地址
     * @param totalAmount 批次總金額
     * @param count 發放筆數
     */
    event BatchApproved(
        bytes32 indexed batchId,
        address indexed approver,
        uint256 totalAmount,
        uint256 count
    );

    /**
     * @dev 批次執行完成事件
     * @param batchId 批次唯一識別碼
     * @param from 執行者地址
     * @param successCount 成功筆數
     * @param failCount 失敗筆數
     */
    event PayoutExecuted(
        bytes32 indexed batchId,
        address indexed from,
        uint256 successCount,
        uint256 failCount
    );

    /**
     * @dev 單筆發放事件
     * @param batchId 批次唯一識別碼
     * @param index 在批次中的索引
     * @param to 收款人地址
     * @param amount 發放金額
     * @param success 是否成功
     * @param data 回傳資料
     */
    event PayoutLine(
        bytes32 indexed batchId,
        uint256 index,
        address to,
        uint256 amount,
        bool success,
        bytes data
    );

    // ============ 建構函式 ============
    /**
     * @dev 初始化合約
     * @param usdc USDC 代幣合約地址
     * @param admin 管理員地址（將獲得所有角色）
     */
    constructor(address usdc, address admin) {
        USDC = usdc;
        
        // 授予管理員所有角色
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(APPROVER_ROLE, admin);
        _grantRole(OPERATOR_ROLE, admin);
    }

    // ============ 管理函式 ============
    /**
     * @dev 設定每月發薪上限
     * @param cap 新的上限金額
     * 
     * 只有 DEFAULT_ADMIN_ROLE 可以調用
     */
    function setMonthlyCap(uint256 cap) external onlyRole(DEFAULT_ADMIN_ROLE) {
        monthlyCap = cap;
    }

    /**
     * @dev 暫停合約（緊急情況使用）
     * 
     * 只有 DEFAULT_ADMIN_ROLE 可以調用
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    /**
     * @dev 恢復合約運作
     * 
     * 只有 DEFAULT_ADMIN_ROLE 可以調用
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // ============ 核心函式 ============
    /**
     * @dev 批次發放薪資
     * @param recipients 收款人地址陣列
     * @param amounts 對應的金額陣列（單位：USDC 最小單位，例如 6 decimals）
     * @param batchId 批次唯一識別碼（防止重複發放）
     * @param meta 批次元資料（例如："2025-11 payroll"）
     * 
     * 要求：
     * - 合約未暫停
     * - 調用者擁有 APPROVER_ROLE
     * - batchId 未被處理過
     * - recipients 和 amounts 長度相同且不為空
     * 
     * 流程：
     * 1. 驗證參數並標記 batchId 為已處理
     * 2. 發出 BatchApproved 事件
     * 3. 逐筆執行轉帳
     * 4. 發出每筆的 PayoutLine 事件
     * 5. 發出 PayoutExecuted 事件總結
     */
    function batchPayout(
        address[] calldata recipients,
        uint256[] calldata amounts,
        bytes32 batchId,
        string calldata meta
    ) external whenNotPaused onlyRole(APPROVER_ROLE) {
        // 驗證批次未被處理過
        require(!processedBatch[batchId], "BATCH_DONE");
        
        // 驗證陣列長度
        require(
            recipients.length == amounts.length && recipients.length > 0,
            "BAD_LEN"
        );
        
        // 標記批次為已處理（防重放）
        processedBatch[batchId] = true;

        // 發出批次批准事件
        emit BatchApproved(batchId, msg.sender, _sum(amounts), recipients.length);

        // 計數器
        uint256 successCount;
        uint256 failCount;
        
        // 逐筆執行轉帳
        for (uint256 i = 0; i < recipients.length; i++) {
            // 使用低階 call 來處理轉帳（更靈活的錯誤處理）
            (bool ok, bytes memory ret) = USDC.call(
                abi.encodeWithSignature(
                    "transfer(address,uint256)",
                    recipients[i],
                    amounts[i]
                )
            );
            
            // 判斷轉帳是否成功
            // 有些代幣不回傳 bool，所以需要檢查 ret.length
            bool lineSuccess = ok && (ret.length == 0 || abi.decode(ret, (bool)) == true);
            
            if (lineSuccess) {
                successCount++;
            } else {
                failCount++;
            }
            
            // 發出單筆發放事件
            emit PayoutLine(batchId, i, recipients[i], amounts[i], lineSuccess, ret);
        }

        // 發出批次執行完成事件
        emit PayoutExecuted(batchId, msg.sender, successCount, failCount);
    }

    // ============ 內部函式 ============
    /**
     * @dev 計算陣列總和
     * @param a 金額陣列
     * @return s 總和
     */
    function _sum(uint256[] memory a) internal pure returns (uint256 s) {
        for (uint256 i = 0; i < a.length; i++) {
            s += a[i];
        }
    }
}

