import discord
import asyncio
import json
import os
from copy import deepcopy
from PIL import Image, ImageDraw, ImageFont
from random import randint
import aiohttp
import io

class Jahy(discord.Client):
  def __init__(self):
    super().__init__()
    self.config = json.load(open("config.json", "r"))
    self.banner_cfg = self.config["Banner"]
    # Load images into memory
    self.images = [i for i in os.listdir(self.banner_cfg["Folder"])]
    self.images = [Image.open(self.banner_cfg["Folder"] + "/" + i) for i in self.images]
    # Load our font
    self.font = ImageFont.truetype(self.config["Font"]["file"], size=self.config["Font"]["size"])

  async def on_ready(self):
    self.channel = self.get_channel(self.config["Channel_ID"])

  def round_corners(self, im, rad):
    """Rounds the corners of the image using a passed radius.

    Straight up ganked from
    https://stackoverflow.com/questions/11287402/how-to-round-corner-a-logo-without-white-backgroundtransparent-on-it-using-pi"""
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

  async def gen_banner(self, member):
    """Generates a banner based on the loaded banners"""
    base = deepcopy(self.images[randint(0, len(self.images) - 1)])

    # Draw the username
    idraw = ImageDraw.Draw(base)
    idraw.text(self.banner_cfg["TextPos"], member.name, fill=tuple(self.banner_cfg["Text_Color"]), font=self.font)
    

    # Get user avatar
    avatar_url = member.avatar_url
    if(avatar_url==None):
      avatar_url = member.default_avatar_url
    # Wow, we can really just load it asynchronously from the API now? That's dope
    avatar = await avatar_url.read()
    # We need to save it as a file in memory to get the size so we can load it as an image.
    with io.BytesIO() as fb:
      fb.write(avatar)
      fb.seek(0, 0)
      avatar = Image.open(fb)
      avatar = avatar.resize(self.banner_cfg["AvatarSize"])
      if (self.banner_cfg["Rounded"]["is_rounded"]):
        avatar = self.round_corners(avatar, self.banner_cfg["Rounded"]["px"])
    # Now that we have our avatar, we can slap it into our banner.
    base.paste(avatar, self.banner_cfg["AvatarPos"])
    
    # Lastly, let's package it as a file to be uploaded.
    with io.BytesIO() as fb:
      base.save(fb, format="png")
      fb.seek(0, 0)
      
      return discord.File(fb, filename="Welcome.png")

  async def on_member_join(self, member):
    banner = await self.gen_banner(member)
    usermap = {"name": member.name, "mention": member.mention}
    await self.channel.send(file=banner)
    await self.channel.send(content=self.config["WelcomeMessage"].format(**usermap))

  def run(self):
    super().run(self.config["Token"])


jahy = Jahy()
jahy.run()
