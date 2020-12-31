from discord.ext import commands


class Fun(commands.Cog):
    @commands.command()
    async def throw(self, ctx, thrower, throwee, thrownat):
        """Throw things, for FUN"""
        await ctx.send(f"{thrower} threw {throwee} at {thrownat}")


def setup(bot):
    bot.add_cog(Fun(bot))
