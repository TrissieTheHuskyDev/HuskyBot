import datetime
import logging
import re

import discord
from discord.ext import commands

from WolfBot import WolfUtils, WolfConfig, WolfStatics

LOG = logging.getLogger("DakotaBot.Utils." + __name__)


class OfflineUserConverter(commands.UserConverter, discord.User):
    """
    Attempt to find a user (either on or off any guild).

    This is a heavy method, and should not be used outside of commands. If a user is not found, it will fail with
    BadArgument.
    """

    # noinspection PyMissingConstructor
    def __init__(self):
        pass

    async def convert(self, ctx: commands.Context, argument: str) -> discord.User:
        result = None

        try:
            result = await super().convert(ctx, argument)
        except commands.BadArgument:
            match = super()._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)

            if match is not None:
                try:
                    result = await ctx.bot.get_user_info(int(match.group(1)))
                except discord.NotFound:
                    result = None

        if result is None:
            LOG.error("Couldn't find offline user matching ID %s. They may have been banned system-wide or"
                      "their ID was typed wrong.", argument)
            raise commands.BadArgument(f'User "{argument}" could not be found. Do they exist?')

        return result


class OfflineMemberConverter(commands.MemberConverter):
    """
    Attempt to find a Member (in the present guild) *or* an offline user (if not in the present guild).

    Be careful, as this method may return User if unexpected (instead of Member).
    """

    async def convert(self, ctx: commands.Context, argument: str) -> discord.User:
        result = None

        try:
            result = await super().convert(ctx, argument)
        except commands.BadArgument:
            match = super()._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)

            if match is not None:
                try:
                    result = await ctx.bot.get_user_info(int(match.group(1)))
                except discord.NotFound:
                    result = None

        if result is None:
            LOG.error("Couldn't find offline user matching ID %s. They may have been banned system-wide or"
                      "their ID was typed wrong.", argument)
            raise commands.BadArgument(f'User "{argument}" could not be found. Do they exist?')

        return result


class DateDiffConverter(datetime.timedelta, commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        if argument in ["0", "perm", "permanent", "inf", "infinite", "-"]:
            return None

        try:
            return WolfUtils.get_timedelta_from_string(argument)
        except ValueError as e:
            raise commands.BadArgument(str(e))


class InviteLinkConverter(str, commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        return WolfUtils.get_fragment_from_invite(argument)


class ChannelContextConverter(dict, commands.Converter):
    async def convert(self, ctx: commands.Context, context: str):
        logging_channel = WolfConfig.get_config() \
            .get('specialChannels', {}).get(WolfStatics.ChannelKeys.STAFF_LOG.value, None)

        channels = []
        name = context

        if context.lower() == "all":
            for channel in ctx.guild.text_channels:
                if channel.id == logging_channel:
                    continue

                channels.append(channel)

        elif context.lower() == "public":
            if not ctx.guild.default_role.permissions.read_messages:
                raise commands.BadArgument("No public channels exist in this guild.")

            for channel in ctx.guild.text_channels:
                if channel.overwrites_for(ctx.guild.default_role).read_messages is False:
                    continue

                channels.append(channel)
        else:
            cl = context.split(',')
            converter = commands.TextChannelConverter()

            for ch_key in cl:
                channels.append(await converter.convert(ctx, ch_key.strip()))

            if len(channels) == 1:
                name = channels[0].name
            else:
                name = str(list(c.name for c in channels))

        return {"name": name, "channels": channels}
