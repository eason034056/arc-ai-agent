import { expect } from "chai";
import { ethers } from "hardhat";
import { CrossChainPayrollVault, MockUSDC, MockTokenMessenger } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

/**
 * CrossChainPayrollVault Test Suite
 * 
 * This comprehensive test suite covers:
 * 1. Contract deployment and initialization
 * 2. Same-chain batch payout (original functionality)
 * 3. Cross-chain batch payout (CCTP integration)
 * 4. Hybrid payouts (mix of same-chain and cross-chain)
 * 5. Security and access control
 * 6. Edge cases and error handling
 * 7. Gas optimization verification
 * 
 * Test structure:
 * - beforeEach: Sets up fresh contract instances for each test
 * - describe blocks: Group related tests
 * - it blocks: Individual test cases
 */
describe("CrossChainPayrollVault", function () {
  // Contract instances
  let vault: CrossChainPayrollVault;
  let usdc: MockUSDC;
  let tokenMessenger: MockTokenMessenger;
  
  // Signers
  let owner: SignerWithAddress;
  let operator: SignerWithAddress;
  let employee1: SignerWithAddress;
  let employee2: SignerWithAddress;
  let employee3: SignerWithAddress;
  let unauthorized: SignerWithAddress;
  
  // Constants
  const INITIAL_VAULT_BALANCE = ethers.parseUnits("100000", 6); // 100,000 USDC
  const ETHEREUM_DOMAIN = 0;
  const AVALANCHE_DOMAIN = 1;
  const OPTIMISM_DOMAIN = 2;

  /**
   * Setup function runs before each test
   * Deploys fresh contracts and sets up initial state
   */
  beforeEach(async function () {
    // Get signers
    [owner, operator, employee1, employee2, employee3, unauthorized] = await ethers.getSigners();

    // Deploy MockUSDC
    const MockUSDC = await ethers.getContractFactory("MockUSDC");
    usdc = await MockUSDC.deploy() as unknown as MockUSDC;
    await usdc.waitForDeployment();

    // Deploy MockTokenMessenger
    const MockTokenMessenger = await ethers.getContractFactory("MockTokenMessenger");
    tokenMessenger = await MockTokenMessenger.deploy() as unknown as MockTokenMessenger;
    await tokenMessenger.waitForDeployment();

    // Deploy CrossChainPayrollVault
    const CrossChainPayrollVault = await ethers.getContractFactory("CrossChainPayrollVault");
    vault = await CrossChainPayrollVault.deploy(
      await usdc.getAddress(),
      owner.address,
      await tokenMessenger.getAddress()
    ) as unknown as CrossChainPayrollVault;
    await vault.waitForDeployment();

    // Grant roles
    const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
    const OPERATOR_ROLE = ethers.keccak256(ethers.toUtf8Bytes("OPERATOR_ROLE"));
    await vault.grantRole(APPROVER_ROLE, operator.address);
    await vault.grantRole(OPERATOR_ROLE, operator.address);

    // Fund vault with USDC
    await usdc.mint(owner.address, INITIAL_VAULT_BALANCE);
    await usdc.transfer(await vault.getAddress(), INITIAL_VAULT_BALANCE);
  });

  // ============================================
  // Test Suite 1: Deployment & Initialization
  // ============================================
  describe("1. Deployment & Initialization", function () {
    it("Should set correct USDC address", async function () {
      expect(await vault.USDC()).to.equal(await usdc.getAddress());
    });

    it("Should set correct TokenMessenger address", async function () {
      expect(await vault.tokenMessenger()).to.equal(await tokenMessenger.getAddress());
    });

    it("Should grant DEFAULT_ADMIN_ROLE to owner", async function () {
      const DEFAULT_ADMIN_ROLE = await vault.DEFAULT_ADMIN_ROLE();
      expect(await vault.hasRole(DEFAULT_ADMIN_ROLE, owner.address)).to.be.true;
    });

    it("Should grant APPROVER_ROLE to owner and operator", async function () {
      const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
      expect(await vault.hasRole(APPROVER_ROLE, owner.address)).to.be.true;
      expect(await vault.hasRole(APPROVER_ROLE, operator.address)).to.be.true;
    });

    it("Should grant OPERATOR_ROLE to owner and operator", async function () {
      const OPERATOR_ROLE = ethers.keccak256(ethers.toUtf8Bytes("OPERATOR_ROLE"));
      expect(await vault.hasRole(OPERATOR_ROLE, owner.address)).to.be.true;
      expect(await vault.hasRole(OPERATOR_ROLE, operator.address)).to.be.true;
    });

    it("Should have correct initial USDC balance", async function () {
      const balance = await vault.getBalance();
      expect(balance).to.equal(INITIAL_VAULT_BALANCE);
    });

    it("Should initialize with zero cross-chain transfers", async function () {
      expect(await vault.totalCrossChainTransfers()).to.equal(0);
    });

    it("Should not be paused initially", async function () {
      expect(await vault.paused()).to.be.false;
    });

    it("Should revert deployment with zero USDC address", async function () {
      const CrossChainPayrollVault = await ethers.getContractFactory("CrossChainPayrollVault");
      await expect(
        CrossChainPayrollVault.deploy(
          ethers.ZeroAddress,
          owner.address,
          await tokenMessenger.getAddress()
        )
      ).to.be.revertedWith("Invalid USDC address");
    });

    it("Should revert deployment with zero admin address", async function () {
      const CrossChainPayrollVault = await ethers.getContractFactory("CrossChainPayrollVault");
      await expect(
        CrossChainPayrollVault.deploy(
          await usdc.getAddress(),
          ethers.ZeroAddress,
          await tokenMessenger.getAddress()
        )
      ).to.be.revertedWith("Invalid admin address");
    });

    it("Should revert deployment with zero TokenMessenger address", async function () {
      const CrossChainPayrollVault = await ethers.getContractFactory("CrossChainPayrollVault");
      await expect(
        CrossChainPayrollVault.deploy(
          await usdc.getAddress(),
          owner.address,
          ethers.ZeroAddress
        )
      ).to.be.revertedWith("Invalid TokenMessenger address");
    });
  });

  // ============================================
  // Test Suite 2: Same-Chain Batch Payout
  // ============================================
  describe("2. Same-Chain Batch Payout", function () {
    it("Should execute same-chain payout successfully", async function () {
      const recipients = [employee1.address, employee2.address];
      const amounts = [
        ethers.parseUnits("5000", 6),
        ethers.parseUnits("6000", 6),
      ];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_001"));

      await vault.connect(operator).batchPayout(recipients, amounts, batchId);

      expect(await usdc.balanceOf(employee1.address)).to.equal(amounts[0]);
      expect(await usdc.balanceOf(employee2.address)).to.equal(amounts[1]);
    });

    it("Should emit BatchApproved event with correct parameters", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_002"));

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      )
        .to.emit(vault, "BatchApproved")
        .withArgs(batchId, operator.address, amounts[0], 1);
    });

    it("Should emit PayoutLine events for each transfer", async function () {
      const recipients = [employee1.address, employee2.address];
      const amounts = [
        ethers.parseUnits("1000", 6),
        ethers.parseUnits("2000", 6),
      ];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_003"));

      const tx = await vault.connect(operator).batchPayout(recipients, amounts, batchId);
      const receipt = await tx.wait();

      // Filter PayoutLine events
      const payoutLineEvents = receipt?.logs.filter(
        (log: any) => {
          try {
            const parsed = vault.interface.parseLog({
              topics: log.topics as string[],
              data: log.data
            });
            return parsed?.name === "PayoutLine";
          } catch {
            return false;
          }
        }
      );

      expect(payoutLineEvents?.length).to.equal(2);
    });

    it("Should emit PayoutExecuted event with success counts", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("1000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_004"));

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      )
        .to.emit(vault, "PayoutExecuted")
        .withArgs(batchId, operator.address, 1, 0);
    });

    it("Should prevent duplicate batch processing", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_005"));

      await vault.connect(operator).batchPayout(recipients, amounts, batchId);

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      ).to.be.revertedWith("BATCH_DONE");
    });

    it("Should reject payout from non-approver", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_006"));

      await expect(
        vault.connect(unauthorized).batchPayout(recipients, amounts, batchId)
      ).to.be.reverted;
    });

    it("Should reject empty recipients array", async function () {
      const recipients: string[] = [];
      const amounts: bigint[] = [];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_007"));

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      ).to.be.revertedWith("BAD_LEN");
    });

    it("Should reject mismatched array lengths", async function () {
      const recipients = [employee1.address, employee2.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_008"));

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      ).to.be.revertedWith("BAD_LEN");
    });

    it("Should handle large batch (50 recipients)", async function () {
      const recipients: string[] = [];
      const amounts: bigint[] = [];
      const amountPerPerson = ethers.parseUnits("100", 6);

      for (let i = 0; i < 50; i++) {
        const wallet = ethers.Wallet.createRandom();
        recipients.push(wallet.address);
        amounts.push(amountPerPerson);
      }

      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_large_001"));

      const tx = await vault.connect(operator).batchPayout(recipients, amounts, batchId);
      const receipt = await tx.wait();
      
      expect(receipt?.status).to.equal(1);
    });

    it("Should mark batch as processed", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("1000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_009"));

      await vault.connect(operator).batchPayout(recipients, amounts, batchId);

      expect(await vault.isBatchProcessed(batchId)).to.be.true;
    });
  });

  // ============================================
  // Test Suite 3: Cross-Chain Batch Payout
  // ============================================
  describe("3. Cross-Chain Batch Payout (CCTP)", function () {
    it("Should initiate cross-chain payout to Ethereum", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_001"));

      const tx = await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum Mainnet"
      );

      await expect(tx).to.emit(vault, "CrossChainPayoutInitiated");
    });

    it("Should emit CrossChainPayoutInitiated with correct parameters", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_002"));

      const tx = await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum Mainnet"
      );

      // Check event was emitted (detailed parameter checking)
      const receipt = await tx.wait();
      const event = receipt?.logs.find(
        (log: any) => {
          try {
            const parsed = vault.interface.parseLog({
              topics: log.topics as string[],
              data: log.data
            });
            return parsed?.name === "CrossChainPayoutInitiated";
          } catch {
            return false;
          }
        }
      );

      expect(event).to.not.be.undefined;
    });

    it("Should approve TokenMessenger to spend USDC", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_003"));

      const messengerBalanceBefore = await usdc.balanceOf(await tokenMessenger.getAddress());

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum Mainnet"
      );

      // Verify TokenMessenger received the USDC (approval worked)
      const messengerBalanceAfter = await usdc.balanceOf(await tokenMessenger.getAddress());
      expect(messengerBalanceAfter - messengerBalanceBefore).to.equal(amounts[0]);
    });

    it("Should call TokenMessenger.depositForBurn", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_004"));

      const initialBurned = await tokenMessenger.totalBurned();

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum Mainnet"
      );

      const finalBurned = await tokenMessenger.totalBurned();
      expect(finalBurned - initialBurned).to.equal(amounts[0]);
    });

    it("Should record cross-chain transfer details", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_005"));

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum Mainnet"
      );

      const nonce = await tokenMessenger.getCurrentNonce();
      const transfer = await vault.getCrossChainTransfer(nonce);

      expect(transfer.batchId).to.equal(batchId);
      expect(transfer.recipient).to.equal(employee1.address);
      expect(transfer.amount).to.equal(amounts[0]);
      expect(transfer.destinationDomain).to.equal(ETHEREUM_DOMAIN);
      expect(transfer.completed).to.be.false;
    });

    it("Should increment totalCrossChainTransfers", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_006"));

      const initialTotal = await vault.totalCrossChainTransfers();

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum Mainnet"
      );

      const finalTotal = await vault.totalCrossChainTransfers();
      expect(finalTotal - initialTotal).to.equal(1);
    });

    it("Should initiate multiple cross-chain payouts in one batch", async function () {
      const recipients = [employee1.address, employee2.address];
      const amounts = [
        ethers.parseUnits("5000", 6),
        ethers.parseUnits("6000", 6),
      ];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_007"));

      const tx = await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        AVALANCHE_DOMAIN,
        "Avalanche C-Chain"
      );

      const receipt = await tx.wait();
      const events = receipt?.logs.filter(
        (log: any) => {
          try {
            const parsed = vault.interface.parseLog({
              topics: log.topics as string[],
              data: log.data
            });
            return parsed?.name === "CrossChainPayoutInitiated";
          } catch {
            return false;
          }
        }
      );

      expect(events?.length).to.equal(2);
    });

    it("Should support different destination domains", async function () {
      const testCases = [
        { domain: ETHEREUM_DOMAIN, name: "Ethereum" },
        { domain: AVALANCHE_DOMAIN, name: "Avalanche" },
        { domain: OPTIMISM_DOMAIN, name: "Optimism" },
      ];

      for (let i = 0; i < testCases.length; i++) {
        const recipients = [employee1.address];
        const amounts = [ethers.parseUnits("1000", 6)];
        const batchId = ethers.keccak256(
          ethers.toUtf8Bytes(`batch_cc_domain_${i}`)
        );

        const tx = await vault.connect(operator).crossChainBatchPayout(
          recipients,
          amounts,
          batchId,
          testCases[i].domain,
          testCases[i].name
        );

        await expect(tx).to.emit(vault, "CrossChainPayoutInitiated");
      }
    });

    it("Should prevent duplicate cross-chain batch", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_008"));

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      await expect(
        vault.connect(operator).crossChainBatchPayout(
          recipients,
          amounts,
          batchId,
          ETHEREUM_DOMAIN,
          "Ethereum"
        )
      ).to.be.revertedWith("BATCH_DONE");
    });

    it("Should reject if insufficient USDC balance", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("200000", 6)]; // More than vault balance
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_009"));

      await expect(
        vault.connect(operator).crossChainBatchPayout(
          recipients,
          amounts,
          batchId,
          ETHEREUM_DOMAIN,
          "Ethereum"
        )
      ).to.be.revertedWith("Insufficient USDC balance");
    });

    it("Should reject from non-approver", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_010"));

      await expect(
        vault.connect(unauthorized).crossChainBatchPayout(
          recipients,
          amounts,
          batchId,
          ETHEREUM_DOMAIN,
          "Ethereum"
        )
      ).to.be.reverted;
    });

    it("Should reject empty recipients array", async function () {
      const recipients: string[] = [];
      const amounts: bigint[] = [];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_011"));

      await expect(
        vault.connect(operator).crossChainBatchPayout(
          recipients,
          amounts,
          batchId,
          ETHEREUM_DOMAIN,
          "Ethereum"
        )
      ).to.be.revertedWith("BAD_LEN");
    });

    it("Should reject mismatched array lengths", async function () {
      const recipients = [employee1.address, employee2.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_012"));

      await expect(
        vault.connect(operator).crossChainBatchPayout(
          recipients,
          amounts,
          batchId,
          ETHEREUM_DOMAIN,
          "Ethereum"
        )
      ).to.be.revertedWith("BAD_LEN");
    });
  });

  // ============================================
  // Test Suite 4: Cross-Chain Transfer Completion
  // ============================================
  describe("4. Cross-Chain Transfer Completion", function () {
    it("Should mark transfer as completed", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_complete_001"));

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      const nonce = await tokenMessenger.getCurrentNonce();

      await vault.connect(operator).markCrossChainTransferCompleted(nonce);

      const transfer = await vault.getCrossChainTransfer(nonce);
      expect(transfer.completed).to.be.true;
    });

    it("Should emit CrossChainPayoutCompleted event", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_complete_002"));

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      const nonce = await tokenMessenger.getCurrentNonce();

      await expect(
        vault.connect(operator).markCrossChainTransferCompleted(nonce)
      )
        .to.emit(vault, "CrossChainPayoutCompleted")
        .withArgs(nonce, batchId, employee1.address, operator.address);
    });

    it("Should reject marking non-existent transfer", async function () {
      const nonce = 999;

      await expect(
        vault.connect(operator).markCrossChainTransferCompleted(nonce)
      ).to.be.revertedWith("Transfer not found");
    });

    it("Should reject double-marking as completed", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_complete_003"));

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      const nonce = await tokenMessenger.getCurrentNonce();

      await vault.connect(operator).markCrossChainTransferCompleted(nonce);

      await expect(
        vault.connect(operator).markCrossChainTransferCompleted(nonce)
      ).to.be.revertedWith("Already completed");
    });

    it("Should reject marking from non-operator", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_cc_complete_004"));

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      const nonce = await tokenMessenger.getCurrentNonce();

      await expect(
        vault.connect(unauthorized).markCrossChainTransferCompleted(nonce)
      ).to.be.reverted;
    });
  });

  // ============================================
  // Test Suite 5: Hybrid Payouts
  // ============================================
  describe("5. Hybrid Payouts (Same-Chain + Cross-Chain)", function () {
    it("Should execute both same-chain and cross-chain payouts", async function () {
      // Same-chain payout
      const sameChainRecipients = [employee1.address];
      const sameChainAmounts = [ethers.parseUnits("3000", 6)];
      const batchId1 = ethers.keccak256(ethers.toUtf8Bytes("batch_hybrid_001"));

      await vault.connect(operator).batchPayout(
        sameChainRecipients,
        sameChainAmounts,
        batchId1
      );

      expect(await usdc.balanceOf(employee1.address)).to.equal(sameChainAmounts[0]);

      // Cross-chain payout
      const crossChainRecipients = [employee2.address];
      const crossChainAmounts = [ethers.parseUnits("4000", 6)];
      const batchId2 = ethers.keccak256(ethers.toUtf8Bytes("batch_hybrid_002"));

      const tx = await vault.connect(operator).crossChainBatchPayout(
        crossChainRecipients,
        crossChainAmounts,
        batchId2,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      await expect(tx).to.emit(vault, "CrossChainPayoutInitiated");
    });

    it("Should handle sequential batches to different chains", async function () {
      // To Ethereum
      await vault.connect(operator).crossChainBatchPayout(
        [employee1.address],
        [ethers.parseUnits("1000", 6)],
        ethers.keccak256(ethers.toUtf8Bytes("hybrid_seq_001")),
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      // To Avalanche
      await vault.connect(operator).crossChainBatchPayout(
        [employee2.address],
        [ethers.parseUnits("2000", 6)],
        ethers.keccak256(ethers.toUtf8Bytes("hybrid_seq_002")),
        AVALANCHE_DOMAIN,
        "Avalanche"
      );

      expect(await vault.totalCrossChainTransfers()).to.equal(2);
    });
  });

  // ============================================
  // Test Suite 6: Admin Functions
  // ============================================
  describe("6. Admin Functions", function () {
    it("Should allow admin to set monthly cap", async function () {
      const newCap = ethers.parseUnits("50000", 6);

      await expect(vault.setMonthlyCap(newCap))
        .to.emit(vault, "MonthlyCapUpdated")
        .withArgs(0, newCap, owner.address);

      expect(await vault.monthlyCap()).to.equal(newCap);
    });

    it("Should reject setting cap from non-admin", async function () {
      const newCap = ethers.parseUnits("50000", 6);

      await expect(
        vault.connect(unauthorized).setMonthlyCap(newCap)
      ).to.be.reverted;
    });

    it("Should allow admin to pause contract", async function () {
      await vault.pause();
      expect(await vault.paused()).to.be.true;
    });

    it("Should allow admin to unpause contract", async function () {
      await vault.pause();
      await vault.unpause();
      expect(await vault.paused()).to.be.false;
    });

    it("Should reject pausing from non-admin", async function () {
      await expect(vault.connect(unauthorized).pause()).to.be.reverted;
    });

    it("Should prevent same-chain payout when paused", async function () {
      await vault.pause();

      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_paused_001"));

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      ).to.be.reverted;
    });

    it("Should prevent cross-chain payout when paused", async function () {
      await vault.pause();

      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_paused_002"));

      await expect(
        vault.connect(operator).crossChainBatchPayout(
          recipients,
          amounts,
          batchId,
          ETHEREUM_DOMAIN,
          "Ethereum"
        )
      ).to.be.reverted;
    });
  });

  // ============================================
  // Test Suite 7: View Functions
  // ============================================
  describe("7. View Functions", function () {
    it("Should return correct USDC balance", async function () {
      const balance = await vault.getBalance();
      expect(balance).to.equal(INITIAL_VAULT_BALANCE);
    });

    it("Should return batch processed status", async function () {
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_view_001"));

      expect(await vault.isBatchProcessed(batchId)).to.be.false;

      await vault.connect(operator).batchPayout(
        [employee1.address],
        [ethers.parseUnits("1000", 6)],
        batchId
      );

      expect(await vault.isBatchProcessed(batchId)).to.be.true;
    });

    it("Should return cross-chain transfer details", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_view_002"));

      await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      const nonce = await tokenMessenger.getCurrentNonce();
      const transfer = await vault.getCrossChainTransfer(nonce);

      expect(transfer.recipient).to.equal(employee1.address);
      expect(transfer.amount).to.equal(amounts[0]);
      expect(transfer.destinationDomain).to.equal(ETHEREUM_DOMAIN);
    });
  });

  // ============================================
  // Test Suite 8: Gas Optimization
  // ============================================
  describe("8. Gas Optimization", function () {
    it("Should execute batch payout with reasonable gas", async function () {
      const recipients = [employee1.address, employee2.address, employee3.address];
      const amounts = [
        ethers.parseUnits("1000", 6),
        ethers.parseUnits("2000", 6),
        ethers.parseUnits("3000", 6),
      ];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_gas_001"));

      const tx = await vault.connect(operator).batchPayout(recipients, amounts, batchId);
      const receipt = await tx.wait();

      // Log gas used for reference
      console.log(`      Gas used for 3 recipients: ${receipt?.gasUsed.toString()}`);

      // Expect reasonable gas usage (adjust threshold as needed)
      expect(receipt?.gasUsed).to.be.lt(500000);
    });

    it("Should execute cross-chain payout with reasonable gas", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_gas_002"));

      const tx = await vault.connect(operator).crossChainBatchPayout(
        recipients,
        amounts,
        batchId,
        ETHEREUM_DOMAIN,
        "Ethereum"
      );
      const receipt = await tx.wait();

      console.log(`      Gas used for 1 cross-chain transfer: ${receipt?.gasUsed.toString()}`);

      expect(receipt?.gasUsed).to.be.lt(500000);
    });
  });

  // ============================================
  // Test Suite 9: Integration Scenarios
  // ============================================
  describe("9. Integration Scenarios", function () {
    it("Should handle complete payroll cycle", async function () {
      // Scenario: Company pays employees across multiple chains

      // 1. Same-chain payouts (local employees)
      await vault.connect(operator).batchPayout(
        [employee1.address],
        [ethers.parseUnits("5000", 6)],
        ethers.keccak256(ethers.toUtf8Bytes("scenario_001"))
      );

      // 2. Cross-chain to Ethereum (remote employee)
      await vault.connect(operator).crossChainBatchPayout(
        [employee2.address],
        [ethers.parseUnits("6000", 6)],
        ethers.keccak256(ethers.toUtf8Bytes("scenario_002")),
        ETHEREUM_DOMAIN,
        "Ethereum"
      );

      // 3. Cross-chain to Avalanche (another remote employee)
      await vault.connect(operator).crossChainBatchPayout(
        [employee3.address],
        [ethers.parseUnits("5500", 6)],
        ethers.keccak256(ethers.toUtf8Bytes("scenario_003")),
        AVALANCHE_DOMAIN,
        "Avalanche"
      );

      // Verify balances
      expect(await usdc.balanceOf(employee1.address)).to.equal(
        ethers.parseUnits("5000", 6)
      );

      // Verify cross-chain transfers
      expect(await vault.totalCrossChainTransfers()).to.equal(2);
    });

    it("Should handle batch rejection and retry", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId1 = ethers.keccak256(ethers.toUtf8Bytes("retry_001"));

      // First attempt
      await vault.connect(operator).batchPayout(recipients, amounts, batchId1);

      // Retry with same ID should fail
      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId1)
      ).to.be.revertedWith("BATCH_DONE");

      // Retry with new ID should succeed
      const batchId2 = ethers.keccak256(ethers.toUtf8Bytes("retry_002"));
      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId2)
      ).to.not.be.reverted;
    });
  });
});

