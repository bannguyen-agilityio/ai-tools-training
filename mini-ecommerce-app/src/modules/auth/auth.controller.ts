import type { RequestHandler } from 'express';
import { sendCreated, sendSuccess } from '../../core/response';
import { authService } from './auth.service';
import type { LoginInput, RegisterInput } from './auth.schemas';

export const register: RequestHandler = async (req, res) => {
  sendCreated(res, await authService.register(req.body as RegisterInput));
};

export const login: RequestHandler = async (req, res) => {
  sendSuccess(res, await authService.login(req.body as LoginInput));
};

export const me: RequestHandler = async (req, res) => {
  sendSuccess(res, await authService.me(req.user!.id));
};
