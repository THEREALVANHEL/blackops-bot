import discord
from discord.ext import commands
from discord import app_commands
import database
import math
import time

class Banking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bank", description="Main banking dashboard.")
    async def bank(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        
        coins = user_data.get("coins", 0)
        bank_balance = user_data.get("bank", 0)
        
        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Bank Dashboard",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Balance", value=f"💰 {coins:,}", inline=True)
        embed.add_field(name="Savings Account", value=f"🏦 {bank_balance:,}", inline=True)
        
        loans = user_data.get("loans", [])
        if loans:
            loan_info = "\n".join([
                f"• {loan['type']} Loan: {loan['amount']:,} coins" for loan in loans
            ])
            embed.add_field(name="Active Loans", value=loan_info, inline=False)
        
        credit_cards = user_data.get("credit_cards", [])
        if credit_cards:
            cc_info = "\n".join([
                f"• {cc['tier']} Card: {cc['limit']:,} limit" for cc in credit_cards
            ])
            embed.add_field(name="Credit Cards", value=cc_info, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    # Savings Account Subcommand Group
    @app_commands.command(name="savings", description="Manage your savings account.")
    @app_commands.describe(action="Deposit or withdraw.", amount="The amount to transfer.")
    @app_commands.choices(
        action=[
            discord.app_commands.Choice(name="deposit", value="deposit"),
            discord.app_commands.Choice(name="withdraw", value="withdraw")
        ]
    )
    async def savings(self, interaction: discord.Interaction, action: str, amount: int):
        user_data = database.db.get_user_data(interaction.user.id)
        
        if amount <= 0:
            await interaction.response.send_message("Please enter a positive amount.", ephemeral=True)
            return

        if action == "deposit":
            if user_data["coins"] < amount:
                await interaction.response.send_message("You don't have enough coins to deposit.", ephemeral=True)
                return
            
            database.db.update_user_data(interaction.user.id, {
                "coins": user_data["coins"] - amount,
                "bank": user_data["bank"] + amount
            })
            await interaction.response.send_message(f"✅ You deposited **{amount:,}** coins into your savings account.")
        
        elif action == "withdraw":
            if user_data["bank"] < amount:
                await interaction.response.send_message("You don't have enough funds in your savings account.", ephemeral=True)
                return
            
            database.db.update_user_data(interaction.user.id, {
                "coins": user_data["coins"] + amount,
                "bank": user_data["bank"] - amount
            })
            await interaction.response.send_message(f"✅ You withdrew **{amount:,}** coins from your savings account.")

    @app_commands.command(name="emicalculator", description="Calculate EMI for a loan.")
    @app_commands.describe(principal="Loan amount.", rate="Annual interest rate (e.g., 10 for 10%).", months="Loan duration in months.")
    async def emi_calculator(self, interaction: discord.Interaction, principal: float, rate: float, months: int):
        if principal <= 0 or rate <= 0 or months <= 0:
            await interaction.response.send_message("All values must be positive.", ephemeral=True)
            return
            
        monthly_rate = (rate / 100) / 12
        emi = (principal * monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
        
        total_interest = emi * months - principal
        
        embed = discord.Embed(
            title="EMI Calculator",
            color=discord.Color.green()
        )
        embed.add_field(name="Monthly EMI", value=f"💰 {emi:,.2f} coins", inline=False)
        embed.add_field(name="Total Interest", value=f"💰 {total_interest:,.2f} coins", inline=False)
        embed.add_field(name="Total Payable", value=f"💰 {emi * months:,.2f} coins", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="creditcard", description="Apply for credit cards with wealth-based limits.")
    @app_commands.describe(tier="The credit card tier you want to apply for.")
    @app_commands.choices(
        tier=[
            discord.app_commands.Choice(name="Basic (2K limit)", value="Basic"),
            discord.app_commands.Choice(name="Silver (7.5K limit)", value="Silver"),
            discord.app_commands.Choice(name="Gold (20K limit)", value="Gold"),
            discord.app_commands.Choice(name="Platinum (50K limit)", value="Platinum")
        ]
    )
    async def creditcard(self, interaction: discord.Interaction, tier: str):
        user_data = database.db.get_user_data(interaction.user.id)
        
        tiers = {
            "Basic": {"limit": 2000, "coins_req": 1000},
            "Silver": {"limit": 7500, "coins_req": 5000},
            "Gold": {"limit": 20000, "coins_req": 15000},
            "Platinum": {"limit": 50000, "coins_req": 40000}
        }
        
        if tier not in tiers:
            await interaction.response.send_message("Invalid credit card tier.", ephemeral=True)
            return
            
        tier_details = tiers[tier]
        
        if user_data["coins"] < tier_details["coins_req"]:
            await interaction.response.send_message(f"You need at least {tier_details['coins_req']:,} coins to apply for a {tier} credit card.", ephemeral=True)
            return
        
        # Add the credit card to the user's data
        user_data["credit_cards"].append({
            "tier": tier,
            "limit": tier_details["limit"],
            "balance": 0
        })
        database.db.update_user_data(interaction.user.id, {"credit_cards": user_data["credit_cards"]})

        await interaction.response.send_message(f"🎉 You have been approved for a **{tier}** credit card with a limit of {tier_details['limit']:,} coins!")

    @app_commands.command(name="loan", description="Apply for loans with different rates.")
    @app_commands.describe(
        amount="The loan amount.",
        type="The type of loan to apply for."
    )
    @app_commands.choices(
        type=[
            discord.app_commands.Choice(name="Personal (15% APR, 30 days)", value="Personal"),
            discord.app_commands.Choice(name="Business (12% APR, 60 days)", value="Business"),
            discord.app_commands.Choice(name="Emergency (20% APR, 14 days)", value="Emergency")
        ]
    )
    async def loan(self, interaction: discord.Interaction, amount: int, type: str):
        user_data = database.db.get_user_data(interaction.user.id)

        loan_types = {
            "Personal": {"apr": 0.15, "duration_days": 30},
            "Business": {"apr": 0.12, "duration_days": 60},
            "Emergency": {"apr": 0.20, "duration_days": 14}
        }

        if type not in loan_types:
            await interaction.response.send_message("Invalid loan type.", ephemeral=True)
            return
        
        loan_details = loan_types[type]
        interest_rate = loan_details["apr"] / 365
        
        # Simple interest calculation
        total_interest = amount * interest_rate * loan_details["duration_days"]
        total_payable = amount + total_interest
        
        # Add loan to user data
        loan_data = {
            "amount": amount,
            "type": type,
            "total_payable": total_payable,
            "due_date": time.time() + (loan_details["duration_days"] * 86400)
        }
        user_data["loans"].append(loan_data)
        database.db.update_user_data(interaction.user.id, {"loans": user_data["loans"]})
        database.db.add_coins(interaction.user.id, amount)

        embed = discord.Embed(
            title="Loan Approved!",
            description=f"Your **{type}** loan for **{amount:,}** coins has been approved.",
            color=discord.Color.green()
        )
        embed.add_field(name="Total Payable", value=f"{total_payable:,.2f} coins", inline=False)
        embed.add_field(name="Due Date", value=f"<t:{int(loan_data['due_date'])}:R>", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="creditscore", description="Detailed credit analysis.")
    async def creditscore(self, interaction: discord.Interaction):
        # Placeholder for credit score command
        await interaction.response.send_message("This command is under development!")

    @app_commands.command(name="paybills", description="Pay monthly bills.")
    async def paybills(self, interaction: discord.Interaction):
        # Placeholder for pay bills command
        await interaction.response.send_message("This command is under development!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Banking(bot))
