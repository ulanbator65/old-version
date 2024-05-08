
Backlog
---------------
Auto-bid: set a min DFLOP limit. When an instance is lost - automatically increase bid price until DFLOP limit is reached.

Calculate cost for each leg in XenBlocks history using saved cost per hour

In the Instance Table view: reset XUNI count also when block count is reset, but skip super.

Auto Miner:
- set a max balance in USD/hour and the Auto Miner tries to mine up to that balance, i.e. purge bad miners, buy new  when budget allows
- configure a minimum DFLOPS


Develop
---------------
-


Verification
---------------
Auto reset

Frequency to minutes from hours in XenBlocks history:
In the Miner Group view, XenBlocks wallet history - change resolution from hours to minutes in the history table
A shorter resoltion will be more accurate as the cost per hour changes frequently and
the calculation errors will be large if too old history values are used

Miner grabber:
quickly grabs any cheap miner offer that shows up
only buys miners, nevers sells - purging have to be done manually



Done
---------------
Implement a State Machine class and use it for XuniMiner
In the Miner Group view: include historic values for cost per hour in the cost calculation
Getting a lot of errors when fetching miner data in Xuni Miner
Auto Miner
DB refactoring


Bugs backlog
----------------






