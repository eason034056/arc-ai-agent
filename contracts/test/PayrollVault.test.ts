import { expect } from "chai";
import { ethers } from "hardhat";
import { PayrollVault, MockUSDC } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("PayrollVault", function () {
  let vault: PayrollVault;
  let usdc: MockUSDC;
  let owner: SignerWithAddress;
  let operator: SignerWithAddress;
  let employee1: SignerWithAddress;
  let employee2: SignerWithAddress;

  beforeEach(async function () {
    // Get signers
    [owner, operator, employee1, employee2] = await ethers.getSigners();

    // Deploy MockUSDC
    const MockUSDC = await ethers.getContractFactory("MockUSDC");
    usdc = await MockUSDC.deploy() as unknown as MockUSDC;
    await usdc.waitForDeployment();

    // Deploy PayrollVault
    const PayrollVault = await ethers.getContractFactory("PayrollVault");
    vault = await PayrollVault.deploy(await usdc.getAddress(), owner.address) as unknown as PayrollVault;
    await vault.waitForDeployment();

    // Grant APPROVER_ROLE to operator
    const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
    await vault.grantRole(APPROVER_ROLE, operator.address);

    // Fund vault with USDC
    const fundAmount = ethers.parseUnits("100000", 6);
    await usdc.mint(owner.address, fundAmount);
    await usdc.transfer(await vault.getAddress(), fundAmount);
  });

  describe("Deployment", function () {
    it("Should set the correct USDC address", async function () {
      expect(await vault.USDC()).to.equal(await usdc.getAddress());
    });

    it("Should grant APPROVER_ROLE to operator", async function () {
      const APPROVER_ROLE = ethers.keccak256(ethers.toUtf8Bytes("APPROVER_ROLE"));
      expect(await vault.hasRole(APPROVER_ROLE, operator.address)).to.be.true;
    });

    it("Should have correct initial balance", async function () {
      const balance = await usdc.balanceOf(await vault.getAddress());
      expect(balance).to.equal(ethers.parseUnits("100000", 6));
    });
  });

  describe("Batch Payout", function () {
    it("Should successfully process batch payout", async function () {
      const recipients = [employee1.address, employee2.address];
      const amounts = [
        ethers.parseUnits("5000", 6),
        ethers.parseUnits("6000", 6),
      ];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_001"));

      // Connect as operator and execute payout
      await vault.connect(operator).batchPayout(recipients, amounts, batchId);

      // Verify balances
      expect(await usdc.balanceOf(employee1.address)).to.equal(amounts[0]);
      expect(await usdc.balanceOf(employee2.address)).to.equal(amounts[1]);
    });

    it("Should emit BatchApproved event", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_002"));

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      )
        .to.emit(vault, "BatchApproved")
        .withArgs(batchId, operator.address, amounts[0], recipients.length);
    });

    it("Should prevent duplicate batch processing", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_003"));

      // First payout should succeed
      await vault.connect(operator).batchPayout(recipients, amounts, batchId);

      // Second payout with same batchId should fail
      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      ).to.be.revertedWith("BATCH_DONE");
    });

    it("Should reject payout from non-approver", async function () {
      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_004"));

      // Employee trying to execute payout should fail
      await expect(
        vault.connect(employee1).batchPayout(recipients, amounts, batchId)
      ).to.be.reverted;
    });
  });

  describe("Admin Functions", function () {
    it("Should allow admin to pause contract", async function () {
      await vault.pause();
      expect(await vault.paused()).to.be.true;
    });

    it("Should prevent payout when paused", async function () {
      await vault.pause();

      const recipients = [employee1.address];
      const amounts = [ethers.parseUnits("5000", 6)];
      const batchId = ethers.keccak256(ethers.toUtf8Bytes("batch_005"));

      await expect(
        vault.connect(operator).batchPayout(recipients, amounts, batchId)
      ).to.be.reverted;
    });
  });
});