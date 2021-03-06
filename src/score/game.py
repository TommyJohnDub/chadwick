#
# $Source$
# $Date: 2007-05-30 21:00:02 -0500 (Wed, 30 May 2007) $
# $Revision: 285 $
#
# DESCRIPTION:
# A container class for the current state of an edited game
# 
# This file is part of Chadwick, a library for baseball play-by-play and stats
# Copyright (C) 2005-2007, Ted Turocy (drarbiter@gmail.com)
#
# This program is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation; either version 2 of the License, or (at 
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
# for more details.
#
# You should have received a copy of the GNU General Public License along 
# with this program; if not, write to the Free Software Foundation, Inc., 
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
# 

import time    # used for setting inputtime in info field
import libchadwick as cw
from boxscore import Boxscore

import wx.lib.newevent
# This event should be posted whenever a change is made to a game
GameUpdateEvent, EVT_GAME_UPDATE = wx.lib.newevent.NewCommandEvent()


def CreateGame(gameId, vis, home):
    """
    Creates a new Chadwick game object, filling in
    informational fields as appropriate.  Assumes that
    'gameId' is in Retrosheet standard format, and 'vis' and
    'home' are the team IDs
    """
    game = cw.Game(gameId)
    
    game.SetVersion("2")
    game.AddInfo("inputprogvers", "Chadwick version 0.5.0")
    game.AddInfo("visteam", vis)
    game.AddInfo("hometeam", home)
    game.AddInfo("date",
                        "%s/%s/%s" % (gameId[3:7],
                                      gameId[7:9],
                                      gameId[9:11]))
    game.AddInfo("number", gameId[-1])

    # Fill in dummy values for other info fields
    # These generally correspond to standards for 'data unknown'
    game.AddInfo("starttime", "0:00")
    game.AddInfo("daynight", "unknown")
    game.AddInfo("site", "")
    game.AddInfo("usedh", "false")
    game.AddInfo("umphome", "")
    game.AddInfo("ump1b", "")
    game.AddInfo("ump2b", "")
    game.AddInfo("ump3b", "")
    game.AddInfo("umplf", "")
    game.AddInfo("umprf", "")
    game.AddInfo("scorer", "")
    game.AddInfo("translator", "")
    game.AddInfo("inputter", "")
    game.AddInfo("inputtime", time.strftime("%Y/%m/%d %I:%M%p"))
    game.AddInfo("howscored", "unknown")
    game.AddInfo("pitches", "none")
    game.AddInfo("temp", "0")
    game.AddInfo("winddir", "unknown")
    game.AddInfo("windspeed", "-1")
    game.AddInfo("fieldcond", "unknown")
    game.AddInfo("precip", "unknown")
    game.AddInfo("sky", "unknown")
    game.AddInfo("timeofgame", "0")
    game.AddInfo("attendance", "0")
    game.AddInfo("wp", "")
    game.AddInfo("lp", "")
    game.AddInfo("save", "")

    return game

class Game:
    def __init__(self, book, game, visRoster, homeRoster):
        self.book = book
        self.game = game
        self.visRoster = visRoster
        self.homeRoster = homeRoster

        self.gameiter = cw.GameIterator(self.game)
        if self.game.first_event != None:  self.gameiter.ToEnd()

        self.boxscore = Boxscore(self.game)

    def GetScorebook(self):   return self.book
    def GetGame(self):        return self.game
    def GetGameID(self):      return self.game.GetGameID()
    
    def GetBoxscore(self):   return self.boxscore
    def BuildBoxscore(self):  self.boxscore.Build()
    
    def AddPlay(self, count, pitches, play):
        self.game.AddEvent(self.GetInning(),
                           self.GetHalfInning(),
                           self.GetCurrentBatter(),
                           count, pitches, play)
        self.gameiter.ToEnd()
        self.boxscore.Build()

    def DeletePlay(self):
        """
        Delete the last play from the game.  This call
        deletes the last actual play (exclusing 'NP'
        placeholder records), to ensure the resulting
        defensive configuration is OK.
        """
        x = self.game.last_event
        while x != None and x.event_text == "NP":
            x = x.prev

        # Now we should be at the last true event.
        # If there isn't one, just complete silently;
        # otherwise, truncate and update everything
        if x != None:
            self.game.Truncate(x)
            self.gameiter.ToEnd()
            self.boxscore.Build()

    def AddSubstitute(self, player, team, slot, pos):
        self.game.AddEvent(self.GetInning(),
                           self.GetHalfInning(),
                           self.GetCurrentBatter(),
                           "??", "", "NP")
        self.game.AddSubstitute(player.GetID(), player.GetName(),
                                team, slot, pos)
        self.gameiter.ToEnd()
        self.boxscore.Build()

    def AddComment(self, text):
        self.game.AddComment(text)

    def GetRoster(self, team):
        if team == 0:  return self.visRoster
        else:          return self.homeRoster
                            
    def SetStarter(self, player, name, team, slot, pos):
        self.game.AddStarter(player, name, team, slot, pos)
        self.gameiter.Reset()

    def GetState(self):   return self.gameiter
    
    def GetCurrentBatter(self):
        halfInning = self.GetHalfInning()

        return self.gameiter.GetPlayer(halfInning,
                                       self.gameiter.NumBatters(halfInning) % 9 + 1)

    def GetCurrentRunner(self, base):
        return self.gameiter.GetRunner(base)

    def GetCurrentPlayer(self, team, slot):
        return self.gameiter.GetPlayer(team, slot)

    def GetCurrentPosition(self, team, slot):
        playerId = self.gameiter.GetPlayer(team, slot)
        return self.gameiter.GetPosition(team, playerId)

    def GetInning(self):        return self.gameiter.GetInning()
    def GetHalfInning(self):    return self.gameiter.GetHalfInning()

    def GetScore(self, team):   return self.gameiter.GetTeamScore(team)
    def GetHits(self, team):    return self.gameiter.GetTeamHits(team)
    def GetErrors(self, team):  return self.gameiter.GetTeamErrors(team)
        
    def GetDoublePlays(self, team):
        return self.boxscore.GetDPs(team)
        
    def GetLOB(self, team):
        """
        Returns the number of runners left on base by 'team'.
        Note that the 'official' definition of this also
        includes any players who have come to bat and are
        still on base.
        """
        return self.gameiter.GetTeamLOB(team)

    def IsLeadoff(self):
        return self.game.first_event == None or self.gameiter.GetOuts() == 3

    def IsGameOver(self):
        event = self.game.last_event
        if event == None:  return False

        if (self.GetInning() >= 9 and self.GetHalfInning() == 1 and
            self.GetScore(1) > self.GetScore(0)):
            return True

        if (self.GetInning() >= 10 and self.GetHalfInning() == 0 and
            event.inning < self.GetInning() and
            self.GetScore(0) > self.GetScore(1)):
            return True
            
        return False
        
    def GetOuts(self):
        if self.gameiter.GetOuts() == 3:
            return 0
        else:
            return self.gameiter.GetOuts()


    def GetInfo(self, tag):
        return self.game.GetInfo(tag)

    def SetInfo(self, tag, value):
        self.game.SetInfo(tag, value)

    def SetER(self, pitcher, value):
        self.game.SetER(pitcher, value)
