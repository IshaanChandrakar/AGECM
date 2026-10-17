export type Reading = {
 id:number; nodeId:string; source:'demo'|'cloud_hardware'; schemaVersion:string; bootId:string; sequence:number;
 channelId:string|null; entryId:number|null; acquiredAt:string; cloudCreatedAt:string|null; receivedAt:string;
 tilt:number|null; displacement:number|null; vibration:number|null; tiltRate:number|null; displacementVelocity:number|null;
 qualityFlags:number; calibrated:boolean; featureReady:boolean; state:string; health:string; ruleVersion:string;
};
export type CloudState={nodeId:string;channelId:string|null;lastEntryId:number;lastSuccessAt:string|null;lastPollAt:string|null;status:string;lastError:string|null;knownGaps:number};
export type SensingNode={id:string;role:string;position:string;latest:Reading|null;health:string;state:string;ageSeconds:number|null;channelConfigured:boolean;expectedReportSeconds:number;cloud:CloudState};
export type SystemStatus={mode:string;source:string;serverTime:string;database:string;expectedReportSeconds:number;staleSeconds:number;nodes:SensingNode[];central:{id:string;role:string;status:string;description:string}};
export type Alert={id:number;nodeId:string;source:string;condition:string;severity:string;triggerText:string;firstOccurredAt:string;lastOccurredAt:string;resolvedAt:string|null;recordId:number|null;ruleVersion:string;qualityFlags:number};
export type Page<T>={content:T[];totalElements:number;totalPages:number;number:number;last:boolean};
