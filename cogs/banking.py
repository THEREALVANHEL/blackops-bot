import discord
from discord.ext import commands
from discord import app_commands
import database
import math
import time
import random
from datetime import datetime, timedelta

class Banking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bank", description="Access your comprehensive banking dashboard.")
    async def bank(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        
        coins = user_data.get("coins", 0)
        bank_balance = user_data.get("bank", 0)
        net_worth = coins + bank_balance
        
        # Calculate interest earned (daily 1% on bank balance)
        last_interest = user_data.get("last_interest", time.time())
        days_passed = (time.time() - last_interest) / 86400
        interest_rate = 0.01  # 1% daily
        potential_interest = bank_balance * interest_rate * days_passed
        
        embed = discord.Embed(
            title=f"🏦 {interaction.user.display_name}'s Banking Dashboard",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Account Overview
        embed.add_field(name="💰 Cash", value=f"`{coins:,}` coins", inline=True)
        embed.add_field(name="🏦 Savings", value=f"`{bank_balance:,}` coins", inline=True)
        embed.add_field(name="💎 Net Worth", value=f"`{net_worth:,}` coins", inline=True)
        
        # Interest Information
        embed.add_field(name="📈 Pending Interest", value=f"`{potential_interest:.0f}` coins", inline=True)
        embed.add_field(name="📊 Interest Rate", value="`1%` per day", inline=True)
        embed.add_field(name="⏰ Last Claimed", value=f"<t:{int(last_interest)}:R>", inline=True)
        
        # Loans and Credit Cards
        loans = user_data.get("loans", [])
        credit_cards = user_data.get("credit_cards", [])
        
        if loans:
            total_debt = sum(loan.get("total_payable", 0) for loan in loans)
            embed.add_field(name="💳 Total Debt", value=f"`{total_debt:,}` coins", inline=True)
            embed.add_field(name="📄 Active Loans", value=f"`{len(loans)}`", inline=True)
        
        if credit_cards:
            total_credit_limit = sum(cc.get("limit", 0) for cc in credit_cards)
            embed.add_field(name="💳 Credit Limit", value=f"`{total_credit_limit:,}` coins", inline=True)
        
        # Credit Score (based on financial behavior)
        credit_score = self._calculate_credit_score(user_data)
        credit_rating = self._get_credit_rating(credit_score)
        embed.add_field(name="⭐ Credit Score", value=f"`{credit_score}` - {credit_rating}", inline=False)
        
        embed.set_footer(text="Use /savings, /loan, /creditcard for more options")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="savings", description="Manage your savings account with interest.")
    @app_commands.describe(action="Deposit, withdraw, or claim interest.", amount="Amount to transfer.")
    @app_commands.choices(
        action=[
            discord.app_commands.Choice(name="💰 Deposit", value="deposit"),
            discord.app_commands.Choice(name="💸 Withdraw", value="withdraw"),
            discord.app_commands.Choice(name="📈 Claim Interest", value="interest")
        ]
    )
    async def savings(self, interaction: discord.Interaction, action: str, amount: int = 0):
        user_data = database.db.get_user_data(interaction.user.id)
        
        if action == "interest":
            # Claim daily interest
            last_interest = user_data.get("last_interest", time.time())
            days_passed = (time.time() - last_interest) / 86400
            
            if days_passed < 1:
                next_claim = last_interest + 86400
                embed = discord.Embed(
                    title="⏰ Interest Not Ready",
                    description=f"You can claim interest again <t:{int(next_claim)}:R>",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            bank_balance = user_data.get("bank", 0)
            interest_rate = 0.01 * min(days_passed, 7)  # Max 7 days of interest
            interest_earned = int(bank_balance * interest_rate)
            
            if interest_earned == 0:
                await interaction.response.send_message("❌ You need money in your savings to earn interest!", ephemeral=True)
                return
            
            new_bank_balance = bank_balance + interest_earned
            database.db.update_user_data(interaction.user.id, {
                "bank": new_bank_balance,
                "last_interest": time.time()
            })
            
            embed = discord.Embed(
                title="📈 Interest Claimed!",
                description=f"**{interaction.user.display_name}** earned interest on their savings!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💰 Interest Earned", value=f"`{interest_earned:,}` coins", inline=True)
            embed.add_field(name="🏦 New Balance", value=f"`{new_bank_balance:,}` coins", inline=True)
            embed.add_field(name="📊 Rate Applied", value=f"`{interest_rate*100:.1f}%`", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Please enter a positive amount.", ephemeral=True)
            return

        if action == "deposit":
            if user_data["coins"] < amount:
                needed = amount - user_data["coins"]
                embed = discord.Embed(
                    title="💸 Insufficient Funds",
                    description=f"You need `{needed:,}` more coins to make this deposit.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            database.db.update_user_data(interaction.user.id, {
                "coins": user_data["coins"] - amount,
                "bank": user_data["bank"] + amount
            })
            
            embed = discord.Embed(
                title="🏦 Deposit Successful",
                description=f"**{interaction.user.display_name}** deposited money into savings!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💰 Deposited", value=f"`{amount:,}` coins", inline=True)
            embed.add_field(name="🏦 New Balance", value=f"`{user_data['bank'] + amount:,}` coins", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
        elif action == "withdraw":
            if user_data["bank"] < amount:
                embed = discord.Embed(
                    title="🏦 Insufficient Savings",
                    description=f"You only have `{user_data['bank']:,}` coins in savings.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            database.db.update_user_data(interaction.user.id, {
                "coins": user_data["coins"] + amount,
                "bank": user_data["bank"] - amount
            })
            
            embed = discord.Embed(
                title="💸 Withdrawal Successful",
                description=f"**{interaction.user.display_name}** withdrew money from savings!",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💰 Withdrawn", value=f"`{amount:,}` coins", inline=True)
            embed.add_field(name="🏦 Remaining", value=f"`{user_data['bank'] - amount:,}` coins", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invest", description="Invest in various options for potential returns.")
    @app_commands.describe(
        investment_type="Type of investment",
        amount="Amount to invest"
    )
    @app_commands.choices(
        investment_type=[
            discord.app_commands.Choice(name="📈 Stocks (High Risk, High Reward)", value="stocks"),
            discord.app_commands.Choice(name="🏠 Real Estate (Medium Risk, Steady)", value="realestate"),
            discord.app_commands.Choice(name="💎 Cryptocurrency (Very High Risk)", value="crypto"),
            discord.app_commands.Choice(name="🏛️ Government Bonds (Low Risk, Low Reward)", value="bonds")
        ]
    )
    async def invest(self, interaction: discord.Interaction, investment_type: str, amount: int):
        user_data = database.db.get_user_data(interaction.user.id)
        
        if amount < 100:
            await interaction.response.send_message("❌ Minimum investment is 100 coins.", ephemeral=True)
            return
        
        if user_data["coins"] < amount:
            await interaction.response.send_message("❌ You don't have enough coins to invest.", ephemeral=True)
            return
        
        # Investment parameters
        investments = {
            "stocks": {"risk": 0.3, "min_return": -0.2, "max_return": 0.4, "time": 3600, "emoji": "📈"},
            "realestate": {"risk": 0.15, "min_return": 0.02, "max_return": 0.15, "time": 7200, "emoji": "🏠"},
            "crypto": {"risk": 0.5, "min_return": -0.4, "max_return": 0.8, "time": 1800, "emoji": "💎"},
            "bonds": {"risk": 0.05, "min_return": 0.01, "max_return": 0.08, "time": 14400, "emoji": "🏛️"}
        }
        
        investment = investments[investment_type]
        
        # Create investment record
        investment_data = {
            "type": investment_type,
            "amount": amount,
            "start_time": time.time(),
            "mature_time": time.time() + investment["time"],
            "expected_return": random.uniform(investment["min_return"], investment["max_return"])
        }
        
        # Store investment
        user_investments = user_data.get("investments", [])
        user_investments.append(investment_data)
        
        database.db.update_user_data(interaction.user.id, {
            "coins": user_data["coins"] - amount,
            "investments": user_investments
        })
        
        mature_timestamp = int(investment_data["mature_time"])
        
        embed = discord.Embed(
            title=f"{investment['emoji']} Investment Made!",
            description=f"**{interaction.user.display_name}** invested in {investment_type.title()}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💰 Invested", value=f"`{amount:,}` coins", inline=True)
        embed.add_field(name="⏰ Matures", value=f"<t:{mature_timestamp}:R>", inline=True)
        embed.add_field(name="📊 Risk Level", value=f"`{investment['risk']*100:.0f}%`", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Use /portfolio to check your investments")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="portfolio", description="View and manage your investment portfolio.")
    async def portfolio(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        investments = user_data.get("investments", [])
        
        if not investments:
            embed = discord.Embed(
                title="📊 Investment Portfolio",
                description="You don't have any investments yet!\nUse `/invest` to start building your portfolio.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Investment Portfolio",
            description=f"**{interaction.user.display_name}'s** Active Investments",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        total_invested = 0
        mature_investments = 0
        
        for i, inv in enumerate(investments[:10]):  # Show up to 10 investments
            total_invested += inv["amount"]
            is_mature = time.time() >= inv["mature_time"]
            
            if is_mature:
                mature_investments += 1
            
            status = "✅ Ready" if is_mature else f"⏳ <t:{int(inv['mature_time'])}:R>"
            
            embed.add_field(
                name=f"{investments[inv['type']]['emoji']} {inv['type'].title()}",
                value=f"**Amount:** `{inv['amount']:,}` coins\n**Status:** {status}",
                inline=True
            )
        
        embed.add_field(name="💰 Total Invested", value=f"`{total_invested:,}` coins", inline=True)
        embed.add_field(name="✅ Ready to Claim", value=f"`{mature_investments}`", inline=True)
        embed.add_field(name="⏳ Pending", value=f"`{len(investments) - mature_investments}`", inline=True)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Use /claiminvestment to claim mature investments")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="claiminvestment", description="Claim returns from mature investments.")
    async def claim_investment(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        investments = user_data.get("investments", [])
        
        if not investments:
            await interaction.response.send_message("❌ You don't have any investments to claim.", ephemeral=True)
            return
        
        mature_investments = [inv for inv in investments if time.time() >= inv["mature_time"]]
        
        if not mature_investments:
            await interaction.response.send_message("❌ None of your investments are ready to claim yet.", ephemeral=True)
            return
        
        total_returns = 0
        total_invested = 0
        claimed_count = 0
        
        for investment in mature_investments:
            invested_amount = investment["amount"]
            return_rate = investment["expected_return"]
            returns = int(invested_amount * (1 + return_rate))
            
            total_invested += invested_amount
            total_returns += returns
            claimed_count += 1
        
        # Remove claimed investments and add returns
        remaining_investments = [inv for inv in investments if time.time() < inv["mature_time"]]
        
        database.db.update_user_data(interaction.user.id, {
            "coins": user_data["coins"] + total_returns,
            "investments": remaining_investments
        })
        
        profit_loss = total_returns - total_invested
        is_profit = profit_loss > 0
        
        embed = discord.Embed(
            title="💰 Investment Returns Claimed!",
            description=f"**{interaction.user.display_name}** claimed {claimed_count} investment(s)",
            color=discord.Color.green() if is_profit else discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💵 Total Invested", value=f"`{total_invested:,}` coins", inline=True)
        embed.add_field(name="💰 Total Returns", value=f"`{total_returns:,}` coins", inline=True)
        embed.add_field(
            name="📊 Profit/Loss", 
            value=f"{'📈' if is_profit else '📉'} `{profit_loss:+,}` coins", 
            inline=True
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="creditcard", description="Apply for credit cards with enhanced features.")
    @app_commands.describe(tier="The credit card tier you want to apply for.")
    @app_commands.choices(
        tier=[
            discord.app_commands.Choice(name="🥉 Bronze (2K limit, 5% cashback)", value="Bronze"),
            discord.app_commands.Choice(name="🥈 Silver (7.5K limit, 3% cashback)", value="Silver"),
            discord.app_commands.Choice(name="🥇 Gold (20K limit, 2% cashback)", value="Gold"),
            discord.app_commands.Choice(name="💎 Platinum (50K limit, 1.5% cashback)", value="Platinum"),
            discord.app_commands.Choice(name="🏆 Black Card (100K limit, 1% cashback)", value="Black")
        ]
    )
    async def creditcard(self, interaction: discord.Interaction, tier: str):
        user_data = database.db.get_user_data(interaction.user.id)
        
        tiers = {
            "Bronze": {"limit": 2000, "coins_req": 1000, "cashback": 0.05, "fee": 0},
            "Silver": {"limit": 7500, "coins_req": 5000, "cashback": 0.03, "fee": 100},
            "Gold": {"limit": 20000, "coins_req": 15000, "cashback": 0.02, "fee": 250},
            "Platinum": {"limit": 50000, "coins_req": 40000, "cashback": 0.015, "fee": 500},
            "Black": {"limit": 100000, "coins_req": 100000, "cashback": 0.01, "fee": 1000}
        }
        
        if tier not in tiers:
            await interaction.response.send_message("❌ Invalid credit card tier.", ephemeral=True)
            return
        
        tier_details = tiers[tier]
        credit_score = self._calculate_credit_score(user_data)
        
        # Credit score requirements
        score_requirements = {
            "Bronze": 300, "Silver": 500, "Gold": 650, "Platinum": 750, "Black": 850
        }
        
        if credit_score < score_requirements[tier]:
            embed = discord.Embed(
                title="❌ Application Denied",
                description=f"Credit score too low for {tier} card.",
                color=discord.Color.red()
            )
            embed.add_field(name="Required Score", value=f"`{score_requirements[tier]}`", inline=True)
            embed.add_field(name="Your Score", value=f"`{credit_score}`", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if user_data["coins"] < tier_details["coins_req"]:
            embed = discord.Embed(
                title="❌ Application Denied",
                description=f"Insufficient funds for {tier} card application.",
                color=discord.Color.red()
            )
            embed.add_field(name="Required", value=f"`{tier_details['coins_req']:,}` coins", inline=True)
            embed.add_field(name="Available", value=f"`{user_data['coins']:,}` coins", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if user already has this tier
        existing_cards = user_data.get("credit_cards", [])
        if any(card["tier"] == tier for card in existing_cards):
            await interaction.response.send_message(f"❌ You already have a {tier} credit card!", ephemeral=True)
            return
        
        # Apply fees
        database.db.remove_coins(interaction.user.id, tier_details["fee"])
        
        # Add the credit card
        new_card = {
            "tier": tier,
            "limit": tier_details["limit"],
            "balance": 0,
            "cashback_rate": tier_details["cashback"],
            "issued_date": time.time(),
            "last_payment": time.time()
        }
        
        existing_cards.append(new_card)
        database.db.update_user_data(interaction.user.id, {"credit_cards": existing_cards})

        embed = discord.Embed(
            title="🎉 Credit Card Approved!",
            description=f"**{interaction.user.display_name}** received a {tier} Credit Card!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💳 Card Tier", value=tier, inline=True)
        embed.add_field(name="💰 Credit Limit", value=f"`{tier_details['limit']:,}` coins", inline=True)
        embed.add_field(name="💸 Cashback Rate", value=f"`{tier_details['cashback']*100:.1f}%`", inline=True)
        embed.add_field(name="💵 Application Fee", value=f"`{tier_details['fee']:,}` coins", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    def _calculate_credit_score(self, user_data: dict) -> int:
        """Calculate credit score based on financial behavior"""
        base_score = 300
        
        # Factors that improve credit score
        bank_balance = user_data.get("bank", 0)
        coins = user_data.get("coins", 0)
        total_wealth = bank_balance + coins
        
        # Wealth factor (up to 200 points)
        wealth_score = min(200, total_wealth // 1000)
        
        # Daily streak factor (up to 150 points)  
        daily_streak = user_data.get("daily_streak", 0)
        streak_score = min(150, daily_streak * 3)
        
        # Work consistency (up to 100 points)
        work_streak = user_data.get("work_streak", 0)
        work_score = min(100, work_streak * 5)
        
        # Loan payment history (can subtract points)
        loans = user_data.get("loans", [])
        loan_penalty = len(loans) * 10  # Penalty for having loans
        
        # Calculate final score
        credit_score = base_score + wealth_score + streak_score + work_score - loan_penalty
        
        return max(300, min(850, credit_score))  # Keep in valid range

    def _get_credit_rating(self, score: int) -> str:
        """Get credit rating based on score"""
        if score >= 800:
            return "Excellent"
        elif score >= 740:
            return "Very Good" 
        elif score >= 670:
            return "Good"
        elif score >= 580:
            return "Fair"
        else:
            return "Poor"

    @app_commands.command(name="loan", description="Apply for loans with enhanced terms.")
    @app_commands.describe(
        amount="The loan amount",
        type="The type of loan to apply for"
    )
    @app_commands.choices(
        type=[
            discord.app_commands.Choice(name="🏠 Personal (12% APR, 30 days)", value="Personal"),
            discord.app_commands.Choice(name="🏢 Business (10% APR, 60 days)", value="Business"),
            discord.app_commands.Choice(name="🚨 Emergency (18% APR, 14 days)", value="Emergency"),
            discord.app_commands.Choice(name="🎓 Education (8% APR, 90 days)", value="Education"),
            discord.app_commands.Choice(name="🏦 Mortgage (6% APR, 180 days)", value="Mortgage")
        ]
    )
    async def loan(self, interaction: discord.Interaction, amount: int, type: str):
        user_data = database.db.get_user_data(interaction.user.id)

        if amount < 100:
            await interaction.response.send_message("❌ Minimum loan amount is 100 coins.", ephemeral=True)
            return

        loan_types = {
            "Personal": {"apr": 0.12, "duration_days": 30, "max_amount": 10000, "min_score": 400},
            "Business": {"apr": 0.10, "duration_days": 60, "max_amount": 50000, "min_score": 500},
            "Emergency": {"apr": 0.18, "duration_days": 14, "max_amount": 5000, "min_score": 300},
            "Education": {"apr": 0.08, "duration_days": 90, "max_amount": 25000, "min_score": 450},
            "Mortgage": {"apr": 0.06, "duration_days": 180, "max_amount": 100000, "min_score": 650}
        }

        if type not in loan_types:
            await interaction.response.send_message("❌ Invalid loan type.", ephemeral=True)
            return
        
        loan_details = loan_types[type]
        credit_score = self._calculate_credit_score(user_data)
        
        # Check credit score requirement
        if credit_score < loan_details["min_score"]:
            embed = discord.Embed(
                title="❌ Loan Application Denied",
                description="Credit score too low for this loan type.",
                color=discord.Color.red()
            )
            embed.add_field(name="Required Score", value=f"`{loan_details['min_score']}`", inline=True)
            embed.add_field(name="Your Score", value=f"`{credit_score}`", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check loan amount limits
        if amount > loan_details["max_amount"]:
            embed = discord.Embed(
                title="❌ Loan Amount Too High",
                description=f"Maximum amount for {type} loans is `{loan_details['max_amount']:,}` coins.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Calculate loan terms
        daily_rate = loan_details["apr"] / 365
        duration_days = loan_details["duration_days"]
        total_interest = amount * daily_rate * duration_days
        total_payable = amount + total_interest
        
        # Credit score affects interest rate (better score = lower rate)
        score_discount = max(0, (credit_score - 300) / 550 * 0.02)  # Up to 2% discount
        adjusted_interest = total_interest * (1 - score_discount)
        adjusted_total = amount + adjusted_interest
        
        # Create loan record
        loan_data = {
            "amount": amount,
            "type": type,
            "total_payable": adjusted_total,
            "interest_rate": loan_details["apr"] - score_discount,
            "due_date": time.time() + (duration_days * 86400),
            "approved_date": time.time(),
            "credit_score_at_approval": credit_score
        }
        
        existing_loans = user_data.get("loans", [])
        existing_loans.append(loan_data)
        
        database.db.update_user_data(interaction.user.id, {"loans": existing_loans})
        database.db.add_coins(interaction.user.id, amount)

        embed = discord.Embed(
            title="🏦 Loan Approved!",
            description=f"**{interaction.user.display_name}** received a {type} loan!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💰 Loan Amount", value=f"`{amount:,}` coins", inline=True)
        embed.add_field(name="💳 Total Payable", value=f"`{adjusted_total:,.0f}` coins", inline=True)
        embed.add_field(name="📊 Interest Rate", value=f"`{(loan_details['apr'] - score_discount)*100:.1f}%` APR", inline=True)
        embed.add_field(name="📅 Due Date", value=f"<t:{int(loan_data['due_date'])}:F>", inline=True)
        embed.add_field(name="⭐ Credit Score", value=f"`{credit_score}` (Discount applied!)", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Loan funds have been added to your account")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="payloan", description="Pay off your loans early or make payments.")
    async def pay_loan(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        loans = user_data.get("loans", [])
        
        if not loans:
            await interaction.response.send_message("❌ You don't have any active loans.", ephemeral=True)
            return
        
        # Show loan payment options
        class LoanPaymentView(discord.ui.View):
            def __init__(self, loans_data):
                super().__init__(timeout=60)
                self.loans_data = loans_data
            
            @discord.ui.select(
                placeholder="Select a loan to pay off...",
                options=[
                    discord.SelectOption(
                        label=f"{loan['type']} - {loan['amount']:,} coins",
                        value=str(i),
                        description=f"Due: {datetime.fromtimestamp(loan['due_date']).strftime('%Y-%m-%d')}"
                    ) for i, loan in enumerate(loans_data[:10])
                ]
            )
            async def loan_select(self, select_interaction, select):
                loan_index = int(select.values[0])
                selected_loan = self.loans_data[loan_index]
                
                payoff_amount = selected_loan['total_payable']
                
                if user_data["coins"] < payoff_amount:
                    embed = discord.Embed(
                        title="❌ Insufficient Funds",
                        description=f"You need `{payoff_amount - user_data['coins']:,.0f}` more coins.",
                        color=discord.Color.red()
                    )
                    await select_interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Pay off loan
                remaining_loans = [loan for i, loan in enumerate(self.loans_data) if i != loan_index]
                
                database.db.update_user_data(interaction.user.id, {
                    "coins": user_data["coins"] - int(payoff_amount),
                    "loans": remaining_loans
                })
                
                embed = discord.Embed(
                    title="✅ Loan Paid Off!",
                    description=f"Successfully paid off your {selected_loan['type']} loan!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Amount Paid", value=f"`{payoff_amount:,.0f}` coins", inline=True)
                embed.add_field(name="Loans Remaining", value=f"`{len(remaining_loans)}`", inline=True)
                
                await select_interaction.response.send_message(embed=embed)
        
        embed = discord.Embed(
            title="💳 Loan Payment Center",
            description="Select a loan to pay off:",
            color=discord.Color.blue()
        )
        
        for i, loan in enumerate(loans[:5]):
            embed.add_field(
                name=f"{loan['type']} Loan",
                value=f"**Amount:** `{loan['total_payable']:,.0f}` coins\n**Due:** <t:{int(loan['due_date'])}:R>",
                inline=True
            )
        
        view = LoanPaymentView(loans)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Banking(bot))
