import discord
import os
from discord.ext import commands, tasks
from collections import defaultdict
from discord.utils import get

from wolframclient.evaluation import WolframLanguageSession, WolframLanguageAsyncSession
from wolframclient.language import wl, wlexpr
from wolframclient.evaluation import SecuredAuthenticationKey, WolframCloudSession
from wolframclient.exception import WolframEvaluationException, WolframLanguageException, WolframKernelException
from PIL import Image
import PIL.ImageOps 
import asyncio
import embeds

from paths import img_path, kernel_path
from functions import eval_input, send_error



# Enlarges image output from Wolfram calculation, and then saves as png #
def enlarge():
    img = Image.open(img_path, 'r')
    img_w, img_h = img.size

    background = Image.new('RGB', (img_w + 25, img_h + 25), (255, 255, 255, 255))
    bg_w, bg_h = background.size
    background.paste(img,(13,12))
    final = PIL.ImageOps.invert(background)
    final.save(img_path)

session = WolframLanguageAsyncSession(kernel_path)
session.start()

class Bark(commands.Cog):

    def __init__(self, client):
        self.client = client

    
    #### Commands ####

    # Echo
    @commands.command()
    @commands.has_any_role('Owners','Moderator', 'Admin')
    async def echo(self, ctx, *, message): ## Repeats message given by user calling the command
        await ctx.channel.purge(limit = 1)
        await ctx.send(f'{message}')
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('We have logged in as {0.user}'.format(self.client))
        
    @commands.command()
    @commands.has_any_role('Admin', 'Bot Henchmen', 'Development Team')
    async def bark(self, ctx,*, script):
        # Prepares the user input to be passed into Wolfram functions that export the output image, and limit the time of the computation 
        async with ctx.typing():
            # export = f'Export["{img_path}", Style[{script}, Large]]'
            try:
                log = await eval_input(script)
                
                # Remove any (' and ') from error messages
                if  '(\'' in log and ('\')' in log or '\',)' in log):
                    log.replace('(\'', '')
                    log.replace('\')', '')

                # Determine output when there's a wolfram error

                if not await send_error(ctx, log):
                    # No errors, continue
                    enlarge()
                    # Send image from Wolfram calculation results
                    await ctx.send(file=discord.File(img_path))

            except Exception:
                await ctx.send(embed = embeds.time_error)
            await session.evaluate(wlexpr('ClearAll["Global`*"]'))
            embeds.tail_message.description = f'Requested by\n{ctx.message.author.mention}'
            await ctx.send(embed = embeds.tail_message)

    @commands.command()
    @commands.has_any_role('Admin', 'Bot Henchmen', 'Development Team')
    async def stop(self, ctx):
        session.terminate()


    # Ping
    @commands.command()
    async def ping(self, ctx):
        bot_latency = round(self.client.latency * 1000)
        if bot_latency <= 50:
            meter = discord.Color.green()
        elif bot_latency < 100:
            meter = discord.Color.gold()
        elif bot_latency >= 100:
            meter  = discord.Color.red()
        elif bot_latency >= 500:
            meter = discord.Color.dark_grey()

        ping_embed = discord.Embed(
            title = f'Woof! {bot_latency} ms',
            color = meter
        )
        ping_embed.set_footer(text = f'requested by {ctx.message.author}', icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed = ping_embed)

def setup(client):
    client.add_cog(Bark(client))