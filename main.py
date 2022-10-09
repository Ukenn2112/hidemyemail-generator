import asyncio
import datetime
from inspect import isclass
import os
from platform import architecture
from typing import Union, List
import re

from rich.text import Text
from rich.prompt import IntPrompt, Prompt, Prompt
from rich.console import Console
from rich.table import Table

from icloud import HideMyEmail


MAX_CONCURRENT_TASKS = 10


class RichHideMyEmail(HideMyEmail):
    _cookie_file = 'cookie.txt'

    def __init__(self):
        super().__init__()
        self.console = Console()
        self.table = Table()

        if os.path.exists(self._cookie_file):
            # load in a cookie string from file
            with open(self._cookie_file, 'r') as f:
                self.cookies = f.read()
        else:
            self.console.log(
                '[bold yellow][WARN][/] 没有找到 "cookie.txt "文件! 由于未经授权的访问，可能无法正常工作。')

    async def _generate_one(self) -> Union[str, None]:
        # First, generate an email
        gen_res = await self.generate_email()

        if not gen_res:
            return
        elif 'success' not in gen_res or not gen_res['success']:
            error = gen_res['error'] if 'error' in gen_res else {}
            err_msg = 'Unknown'
            if type(error) == int and 'reason' in gen_res:
                err_msg = gen_res['reason']
            elif type(error) == dict and 'errorMessage' in error:
                err_msg = error['errorMessage']
            self.console.log(
                f'[bold red][ERR][/] - 生成匿名邮箱失败。原因是: {err_msg}')
            return

        email = gen_res['result']['hme']
        self.console.log(f'[50%] "{email}" - 成功生成，正在激活...')

        # Then, reserve it
        reserve_res = await self.reserve_email(email)

        if not reserve_res:
            return
        elif 'success' not in reserve_res or not reserve_res['success']:
            error = reserve_res['error'] if 'error' in reserve_res else {}
            err_msg = 'Unknown'
            if type(error) == int and 'reason' in reserve_res:
                err_msg = reserve_res['reason']
            elif type(error) == dict and 'errorMessage' in error:
                err_msg = error['errorMessage']
            self.console.log(
                f'[bold red][ERR][/] "{email}" - 激活匿名邮箱失败。原因是: {err_msg}')
            return

        self.console.log(f'[100%] "{email}" - 激活成功')
        return email

    async def _generate(self, num: int):
        tasks = []
        for _ in range(num):
            task = asyncio.ensure_future(self._generate_one())
            tasks.append(task)

        return filter(lambda e: e is not None, await asyncio.gather(*tasks))

    async def generate(self) -> List[str]:
        try:
            emails = []
            self.console.rule()
            s = IntPrompt.ask(
                Text.assemble(("你想生成多少个 iCloud 匿名邮箱？回车默认")), default=1, console=self.console)

            self.label = Prompt.ask(
                Text.assemble(("设置匿名邮箱在 iCloud 的标签 (备注) 回车默认")), default="rtuna's gen", console=self.console)

            count = int(s)
            self.console.log(f'正在生成 {count} 个匿名邮箱中...')
            self.console.rule()

            with self.console.status(f"[bold green]开始生成 iCloud 匿名邮箱..."):
                while count > 0:
                    batch = await self._generate(count if count < MAX_CONCURRENT_TASKS else MAX_CONCURRENT_TASKS)
                    count -= MAX_CONCURRENT_TASKS
                    emails += batch

            if len(emails) > 0:
                with open('emails.txt', 'a+') as f:
                    f.write(os.linesep.join(emails) + os.linesep)

                self.console.rule()
                self.console.log(
                    f':star: 生成的匿名邮箱已被保存到 "emails.txt "文件中')

                self.console.log(
                    f'[bold green]任务完成![/] 成功生成匿名邮箱共 [bold green]{len(emails)}[/] 个')

            return emails
        except KeyboardInterrupt:
            return []

    async def list(self, active, search) -> List[str]:
        gen_res = await self.list_email()
        if not gen_res:
            return
        elif 'success' not in gen_res or not gen_res['success']:
            error = gen_res['error'] if 'error' in gen_res else {}
            err_msg = 'Unknown'
            if type(error) == int and 'reason' in gen_res:
                err_msg = gen_res['reason']
            elif type(error) == dict and 'errorMessage' in error:
                err_msg = error['errorMessage']
            self.console.log(
                f'[bold red][ERR][/] - 生成匿名邮箱失败。原因是: {err_msg}')
            return


        self.table.add_column("Label")
        self.table.add_column("Hide my email")
        self.table.add_column("Created Date Time")
        self.table.add_column("IsActive")
        
        for row in gen_res["result"]["hmeEmails"]:
    
            if row["isActive"] == active:
                if search is not None:
                    if re.search(search, row["label"]): 
                        self.table.add_row(row["label"], row["hme"],            
                        str(datetime.datetime.fromtimestamp(row["createTimestamp"]/1000)),
                        str(row["isActive"]))           
                else:
                    self.table.add_row(row["label"], row["hme"],            
                    str(datetime.datetime.fromtimestamp(row["createTimestamp"]/1000)),
                    str(row["isActive"]))


        self.console.print(self.table)




async def generate():
    async with RichHideMyEmail() as i:       
        await i.generate()

async def list(active, search):
    async with RichHideMyEmail() as i:       
        await i.list(active, search)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate())
