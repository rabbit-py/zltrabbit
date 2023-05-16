# -*- coding: utf-8 -*-

from sms.SmsInterface import SmsInterface
import httpx
import asyncio


class ShilaiSms(SmsInterface):

    async def send_code(self, phoneNumbers: list, use_template: str) -> bool:
        code = self.generate_code()
        template_code = self._config.get("template_code").get(use_template)
        tasks = []
        for phoneNumber in phoneNumbers:
            tasks.append(asyncio.create_task(self.save_code(str(phoneNumber), code, expire=self._config.get("expire", 300))))
        await asyncio.gather(*tasks)
        return await self.send_sms(phoneNumbers, template_code, {"code": code})

    async def send_sms(self, phoneNumbers: list, template_code: str, template_param: dict = {}) -> bool:
        response = await httpx.AsyncClient().post(self._config["url"],
                                                  json={
                                                      "phoneNumbers": phoneNumbers,
                                                      "templateCode": template_code,
                                                      "templateParams": template_param
                                                  })
        return response.status_code == 200